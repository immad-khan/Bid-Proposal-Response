'use client';

import React, { useMemo, useState, useCallback, useEffect, useRef } from 'react';
import { createEditor, Descendant, Transforms, Editor, Element as SlateElement, Text } from 'slate';
import { Slate, Editable, withReact, useSlate } from 'slate-react';
import { 
  Bold, Italic, List, ListOrdered, Save, 
  MessageSquare, User, Send, CheckCircle 
} from 'lucide-react';

// Define custom types for Slate elements
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

interface InlineDocumentEditorProps {
  initialContentJson: string;
  workspaceId: string;
  onSave: (contentJson: string, comment: string) => Promise<any>;
  versionNumber: number;
}

interface CommentThread {
  id: string;
  user: string;
  text: string;
  timestamp: string;
}

export default function InlineDocumentEditor({
  initialContentJson,
  workspaceId,
  onSave,
  versionNumber
}: InlineDocumentEditorProps) {
  const editor = useMemo(() => withReact(createEditor()), []);
  
  // Parse initial content JSON, fallback if invalid
  const initialValue = useMemo<Descendant[]>(() => {
    try {
      if (initialContentJson) {
        const parsed = JSON.parse(initialContentJson);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn("Invalid Slate JSON content, falling back to default paragraph.");
    }
    return [
      {
        type: 'paragraph',
        children: [{ text: 'NASA Deep Space Communication System Proposal. Section 1: Introduction. We propose a cognitive radio system operating in the Ka-band. Performance metrics exceed JPL specifications by 15%.' }]
      }
    ];
  }, [initialContentJson]);

  const [value, setValue] = useState<Descendant[]>(initialValue);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [charCount, setCharCount] = useState(0);
  const [comments, setComments] = useState<CommentThread[]>([
    { id: '1', user: 'jane_doe', text: 'Section 1 needs additional details about Ka-band RF power output.', timestamp: '10 mins ago' },
    { id: '2', user: 'admin', text: 'Added technical transceiver details in v2. Please review compliance.', timestamp: 'Just now' }
  ]);
  const [newCommentText, setNewCommentText] = useState('');
  
  // Save comment input
  const saveComment = () => {
    if (!newCommentText.trim()) return;
    setComments([
      ...comments,
      {
        id: Date.now().toString(),
        user: 'admin',
        text: newCommentText,
        timestamp: 'Just now'
      }
    ]);
    setNewCommentText('');
  };

  // Render elements for Slate
  const renderElement = useCallback((props: any) => {
    switch (props.element.type) {
      case 'bulleted-list':
        return <ul className="list-disc pl-5 mb-4 text-slate-300" {...props.attributes}>{props.children}</ul>;
      case 'numbered-list':
        return <ol className="list-decimal pl-5 mb-4 text-slate-300" {...props.attributes}>{props.children}</ol>;
      case 'list-item':
        return <li className="mb-1 text-slate-300" {...props.attributes}>{props.children}</li>;
      default:
        return <p className="mb-4 text-slate-300 leading-relaxed" {...props.attributes}>{props.children}</p>;
    }
  }, []);

  // Render leaf nodes for styles (bold, italic)
  const renderLeaf = useCallback((props: any) => {
    let el = props.children;
    if (props.leaf.bold) {
      el = <strong className="font-bold text-slate-100">{el}</strong>;
    }
    if (props.leaf.italic) {
      el = <em className="italic text-slate-200">{el}</em>;
    }
    return <span {...props.attributes}>{el}</span>;
  }, []);

  // Calculate live characters count
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

  // Debounced Auto-save implementation
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const handleEditorChange = (newValue: Descendant[]) => {
    setValue(newValue);
    setSaveStatus('saving');

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

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

  // Clean timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Formatting Toolbar action helpers
  const isMarkActive = (editor: Editor, format: string) => {
    const marks: any = Editor.marks(editor);
    return marks ? marks[format] === true : false;
  };

  const toggleMark = (editor: Editor, format: string) => {
    const isActive = isMarkActive(editor, format);
    if (isActive) {
      Editor.removeMark(editor, format);
    } else {
      Editor.addMark(editor, format, true);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 bg-slate-950 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
      {/* Slate Editor Container */}
      <div className="lg:col-span-3 flex flex-col min-h-[500px]">
        {/* Editor Header / Save Indicator */}
        <div className="bg-slate-900 px-6 py-4 flex justify-between items-center border-b border-slate-850">
          <div>
            <h3 className="text-slate-200 font-bold text-sm flex items-center gap-2">
              Proposal Response Editor
              <span className="bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-emerald-500/20">
                v{versionNumber}
              </span>
            </h3>
            <p className="text-slate-400 text-xs mt-0.5">Auto-saves changes when typing ceases.</p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Auto-save status indicator */}
            <div className="text-xs flex items-center gap-1.5">
              {saveStatus === 'saving' && (
                <span className="flex items-center gap-1.5 text-amber-400">
                  <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-ping" />
                  Auto-saving...
                </span>
              )}
              {saveStatus === 'saved' && (
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <CheckCircle className="w-3.5 h-3.5" />
                  Saved to Cloud
                </span>
              )}
              {saveStatus === 'idle' && (
                <span className="text-slate-500">All changes saved</span>
              )}
            </div>
            
            <div className="text-xs text-slate-400 font-medium border-l border-slate-800 pl-4">
              {charCount} characters
            </div>
          </div>
        </div>

        {/* Format Toolbar */}
        <div className="bg-slate-900/60 px-4 py-2 border-b border-slate-850 flex gap-1.5 items-center">
          <button
            onMouseDown={(e) => {
              e.preventDefault();
              toggleMark(editor, 'bold');
            }}
            className={`p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors ${
              isMarkActive(editor, 'bold') ? 'bg-slate-800 text-emerald-400' : ''
            }`}
            title="Bold (Ctrl+B)"
          >
            <Bold className="w-4 h-4" />
          </button>
          
          <button
            onMouseDown={(e) => {
              e.preventDefault();
              toggleMark(editor, 'italic');
            }}
            className={`p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors ${
              isMarkActive(editor, 'italic') ? 'bg-slate-800 text-emerald-400' : ''
            }`}
            title="Italic (Ctrl+I)"
          >
            <Italic className="w-4 h-4" />
          </button>
        </div>

        {/* Editable Workspace */}
        <div className="flex-1 p-6 overflow-y-auto bg-slate-950/20 max-h-[600px] scrollbar-thin scrollbar-thumb-slate-800">
          <Slate editor={editor} initialValue={initialValue} onChange={handleEditorChange}>
            <Editable
              renderElement={renderElement}
              renderLeaf={renderLeaf}
              placeholder="Draft your proposal response here..."
              className="outline-none min-h-[350px] font-sans text-slate-300 text-sm focus:ring-0"
              style={{ caretColor: '#10b981' }}
            />
          </Slate>
        </div>
      </div>

      {/* Collaboration Sidebar (Comments) */}
      <div className="lg:col-span-1 bg-slate-900/30 border-l border-slate-800/80 flex flex-col justify-between min-h-[500px]">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-850 bg-slate-900/40">
          <h4 className="text-slate-200 font-bold text-xs flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-emerald-400" />
            Comments & Feedback
          </h4>
          <p className="text-slate-500 text-[10px] mt-0.5">RFP review discussions.</p>
        </div>

        {/* Comments Stream */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4 max-h-[400px]">
          {comments.map((comm) => (
            <div key={comm.id} className="bg-slate-950/60 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 hover:border-slate-800 transition-colors">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1.5">
                  <div className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-[10px] text-slate-300 font-bold uppercase">
                    {comm.user.charAt(0)}
                  </div>
                  <span className="text-slate-300 text-[11px] font-bold">{comm.user}</span>
                </div>
                <span className="text-slate-500 text-[9px]">{comm.timestamp}</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">{comm.text}</p>
            </div>
          ))}
        </div>

        {/* Comment Input */}
        <div className="p-4 border-t border-slate-850 bg-slate-900/40">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Add feedback/comment..."
              value={newCommentText}
              onChange={(e) => setNewCommentText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && saveComment()}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 transition-colors"
            />
            <button
              onClick={saveComment}
              className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 flex items-center justify-center transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
