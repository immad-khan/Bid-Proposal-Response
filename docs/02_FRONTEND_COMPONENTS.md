# File: `frontend/components/InlineDocumentEditor.tsx` & `VersionDiff.tsx`

This document details the frontend Slate.js editor component and the version diffing comparison component.

---

## 📝 1. `frontend/components/InlineDocumentEditor.tsx`

This component implements a rich text proposal editor utilizing **Slate.js** (a customizable framework for building rich text editors). It supports real-time editing, local auto-saving, char-counting, and a sidebar for commenting and team feedback.

### Types and Type System Extensions
Slate.js requires extending the global TypeScript types module to recognize custom block elements:
```typescript
type CustomText = { text: string; bold?: boolean; italic?: boolean };
type ParagraphElement = { type: 'paragraph'; children: CustomText[] };
type BulletedListElement = { type: 'bulleted-list'; children: CustomText[] };
type NumberedListElement = { type: 'numbered-list'; children: CustomText[] };
type ListItemElement = { type: 'list-item'; children: CustomText[] };

type CustomElement = ParagraphElement | BulletedListElement | NumberedListElement | ListItemElement;

declare module 'slate' {
  interface CustomTypes {
    Editor: import('slate-react').ReactEditor;
    Element: CustomElement;
    Text: CustomText;
  }
}
```

### Component Props
```typescript
interface InlineDocumentEditorProps {
  initialContentJson: string; // The draft content stored in database as JSON
  workspaceId: string;        // Target workspace identifier
  onSave: (contentJson: string, comment: string) => Promise<any>; // Save callback
  versionNumber: number;      // Current version indicator
}
```

### State Variables
* **`value` (`Descendant[]`)**: The live internal state of the Slate editor.
* **`saveStatus` (`'idle' | 'saving' | 'saved'`)**: Tracks the auto-save worker state to render user visual status rings.
* **`charCount` (`number`)**: Real-time count of non-formatting characters within the editor block.
* **`comments` (`CommentThread[]`)**: Array of discussion points. Instantiated with two mock items and populated by the input container.
* **`newCommentText` (`string`)**: Controlled text input string for new comments.

---

### Core Mechanics & Event Handlers

#### A. Initial State Resolution
```typescript
const initialValue = useMemo<Descendant[]>(() => {
  try {
    if (initialContentJson) {
      const parsed = JSON.parse(initialContentJson);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {
    console.warn("Invalid Slate JSON content, falling back to default paragraph.");
  }
  return [{ type: 'paragraph', children: [{ text: 'NASA Deep Space Communication System Proposal...' }] }];
}, [initialContentJson]);
```
Safely parses JSON database strings. If parsing fails, it returns a default paragraph to prevent the editor screen from crashing.

#### B. Slate Element & Leaf Renderers
* **`renderElement` (`useCallback`)**: Resolves structural HTML tags for formatting nodes (`bulleted-list` -> `<ul>`, `numbered-list` -> `<ol>`, `list-item` -> `<li>`, default -> `<p>`).
* **`renderLeaf` (`useCallback`)**: Applies text styles (bolding wraps inside `<strong>`, italicizing inside `<em>`).

#### C. Character Count Aggregator
```typescript
useEffect(() => {
  const serialize = (nodes: Descendant[]): string => {
    return nodes.map(n => {
      if (Text.isText(n)) return n.text;
      if (n.children) return serialize(n.children);
      return '';
    }).join('');
  };
  setCharCount(serialize(value).length);
}, [value]);
```
Recursively extracts leaf strings across nested nodes to count typed characters.

#### D. Debounced Auto-Save
```typescript
const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

const handleEditorChange = (newValue: Descendant[]) => {
  setValue(newValue);
  setSaveStatus('saving');

  if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);

  saveTimeoutRef.current = setTimeout(async () => {
    try {
      const contentStr = JSON.stringify(newValue);
      await onSave(contentStr, `Auto-saved changes at ${new Date().toLocaleTimeString()}`);
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (err) {
      console.error('Auto-save failed:', err);
      setSaveStatus('idle');
    }
  }, 1500); // 1.5 seconds delay after user stops typing
};
```
Listens to character inputs. Every keypress clears the previous timeout. Once the user stops typing for 1.5 seconds, the editor automatically persists the draft JSON string to the .NET database via the `onSave` hook, without requiring a manual save button.

#### E. Rich Text Toolbar Helpers
* **`isMarkActive(editor, format)`**: Interrogates the active Slate cursor selection to check if a specific format mark (bold/italic) is applied.
* **`toggleMark(editor, format)`**: Adds or removes formatting attributes (e.g., Bold/Italic) on selected text.

---

## 🔍 2. `frontend/components/VersionDiff.tsx`

This component compares two workspace version drafts and visualizes the exact differences (additions and deletions).

### Component Props
```typescript
interface VersionDiffProps {
  oldContentJson: string;   // Original snapshot content
  newContentJson: string;   // Target comparison snapshot content
  oldVersionLabel: string;  // Left comparison label (e.g. "v1")
  newVersionLabel: string;  // Right comparison label (e.g. "v2")
}
```

### Slate JSON to Plain Text Converter
```typescript
function slateJsonToText(jsonStr: string): string {
  try {
    if (!jsonStr) return '';
    const parsed = JSON.parse(jsonStr);
    if (Array.isArray(parsed)) {
      return parsed.map((node: any) => {
        if (node.text) return node.text;
        if (node.children && Array.isArray(node.children)) {
          return node.children.map((child: any) => child.text || '').join('');
        }
        return '';
      }).join('\n');
    }
  } catch (e) {}
  return jsonStr;
}
```
Converts complex nested Slate JSON structures into raw, newline-delimited text strings so they can be processed by the diff algorithm.

### LCS (Longest Common Subsequence) Diff Algorithm
```typescript
function computeLineDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  const m = oldLines.length;
  const n = newLines.length;
  
  // DP matrix for Longest Common Subsequence
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
  
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  
  const diffResult: DiffLine[] = [];
  let i = m, j = n;
  
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      diffResult.unshift({ type: 'unchanged', value: oldLines[i - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      diffResult.unshift({ type: 'added', value: newLines[j - 1] });
      j--;
    } else {
      diffResult.unshift({ type: 'removed', value: oldLines[i - 1] });
      i--;
    }
  }
  return diffResult;
}
```

#### Algorithm Breakdown
1. **Splitting:** Divides both documents into line arrays.
2. **DP Matrix:** Dynamically tracks matches to discover the longest matching block subsequence.
3. **Backtracking:** Walks backward from `(m, n)` to `(0, 0)`:
   - Identical lines are added as `unchanged`.
   - New lines that were inserted are marked as `added`.
   - Lines that no longer exist are marked as `removed`.
4. **Rendering:** Highlights additions in light green (with a `+` prefix) and deletions in red with a strikethrough (with a `-` prefix).
