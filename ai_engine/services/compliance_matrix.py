"""
Compliance Matrix Service — Neo4j graph database client.
Stores RFP requirements and proposal sections as graph nodes and links them
with COMPLIES_WITH relationships to enable compliance tracking and gap analysis.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class ComplianceMatrixService:
    """
    Neo4j client for constructing and querying the compliance graph.
    Nodes: Requirement, ProposalSection
    Relationships: COMPLIES_WITH (status: COMPLIANT | PARTIAL | NON_COMPLIANT)
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")

        logger.info(f"ComplianceMatrixService: Connecting to Neo4j at {self.uri}")
        self._driver = GraphDatabase.driver(
            self.uri, auth=(self.username, self.password)
        )
        # Verify connectivity
        self._driver.verify_connectivity()
        logger.info("ComplianceMatrixService: Connected successfully.")

    def close(self):
        """Close the Neo4j driver connection."""
        self._driver.close()
        logger.info("ComplianceMatrixService: Connection closed.")

    # ─────────────────── Write Operations ───────────────────

    def create_requirement_node(
        self,
        requirement_id: str,
        section_path: str,
        description: str,
        is_mandatory: bool = True,
        page_ref: Optional[int] = None,
    ):
        """
        Create or merge a Requirement node in the graph.

        Args:
            requirement_id: Unique requirement identifier (e.g. REQ_001).
            section_path: Section hierarchy path (e.g. 'Technical > Security > ISO 27001').
            description: Full requirement text.
            is_mandatory: Whether the requirement is mandatory.
            page_ref: Source page number in the RFP document.
        """
        query = """
        MERGE (r:Requirement {id: $req_id})
        SET r.section_path  = $section_path,
            r.description   = $description,
            r.is_mandatory   = $is_mandatory,
            r.page_reference = $page_ref,
            r.updated_at     = datetime()
        RETURN r.id AS id
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                req_id=requirement_id,
                section_path=section_path,
                description=description,
                is_mandatory=is_mandatory,
                page_ref=page_ref,
            )
            record = result.single()
            logger.info(f"ComplianceMatrixService: Upserted Requirement [{record['id']}]")

    def create_proposal_section_node(
        self, section_id: str, title: str, content_preview: str = ""
    ):
        """
        Create or merge a ProposalSection node.

        Args:
            section_id: Unique section identifier.
            title: Section heading.
            content_preview: First 500 chars of the draft for quick reference.
        """
        query = """
        MERGE (p:ProposalSection {id: $section_id})
        SET p.title           = $title,
            p.content_preview = $content_preview,
            p.updated_at      = datetime()
        RETURN p.id AS id
        """
        with self._driver.session() as session:
            result = session.run(
                query, section_id=section_id, title=title, content_preview=content_preview
            )
            record = result.single()
            logger.info(f"ComplianceMatrixService: Upserted ProposalSection [{record['id']}]")

    def link_compliance(
        self,
        proposal_section_id: str,
        requirement_id: str,
        status: str = "COMPLIANT",
        evidence: str = "",
        score: float = 1.0,
    ):
        """
        Create a COMPLIES_WITH relationship between a ProposalSection and a Requirement.

        Args:
            proposal_section_id: The proposal section node ID.
            requirement_id: The requirement node ID.
            status: One of COMPLIANT, PARTIAL, NON_COMPLIANT.
            evidence: Supporting evidence text or chunk reference.
            score: Numeric compliance score (0.0 – 1.0).
        """
        query = """
        MATCH (p:ProposalSection {id: $pid})
        MATCH (r:Requirement {id: $rid})
        MERGE (p)-[rel:COMPLIES_WITH]->(r)
        SET rel.status     = $status,
            rel.evidence   = $evidence,
            rel.score      = $score,
            rel.updated_at = datetime()
        RETURN p.id AS pid, r.id AS rid, rel.status AS status
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                pid=proposal_section_id,
                rid=requirement_id,
                status=status,
                evidence=evidence,
                score=score,
            )
            record = result.single()
            if record:
                logger.info(
                    f"ComplianceMatrixService: Linked [{record['pid']}] → [{record['rid']}] "
                    f"(Status: {record['status']})"
                )
            else:
                logger.warning(
                    f"ComplianceMatrixService: Could not link {proposal_section_id} → "
                    f"{requirement_id}. Check that both nodes exist."
                )

    def create_evidence_node(self, evidence_id: str, title: str, document_url: str = ""):
        """Create or merge an Evidence node."""
        query = """
        MERGE (e:Evidence {id: $evidence_id})
        SET e.title        = $title,
            e.document_url = $document_url,
            e.updated_at   = datetime()
        RETURN e.id AS id
        """
        with self._driver.session() as session:
            result = session.run(query, evidence_id=evidence_id, title=title, document_url=document_url)
            logger.info(f"ComplianceMatrixService: Upserted Evidence [{result.single()['id']}]")

    def link_evidence(self, requirement_id: str, evidence_id: str):
        """Link Evidence to Requirement via SATISFIED_BY edge."""
        query = """
        MATCH (r:Requirement {id: $rid})
        MATCH (e:Evidence {id: $eid})
        MERGE (r)<-[rel:SATISFIED_BY]-(e)
        SET rel.updated_at = datetime()
        RETURN r.id AS rid, e.id AS eid
        """
        with self._driver.session() as session:
            result = session.run(query, rid=requirement_id, eid=evidence_id)
            if result.single():
                logger.info(f"ComplianceMatrixService: Linked Evidence [{evidence_id}] → Requirement [{requirement_id}]")
            else:
                logger.warning("ComplianceMatrixService: Failed to link Evidence to Requirement.")

    # ─────────────────── Read Operations ───────────────────

    def get_compliance_matrix(self) -> List[Dict[str, Any]]:
        """
        Retrieve the full compliance matrix — all requirement-to-proposal mappings.

        Returns:
            List of dicts with requirement_id, section_path, status,
            proposal_section, evidence, and score.
        """
        query = """
        MATCH (p:ProposalSection)-[rel:COMPLIES_WITH]->(r:Requirement)
        RETURN r.id              AS requirement_id,
               r.section_path    AS section_path,
               r.is_mandatory    AS is_mandatory,
               rel.status        AS status,
               rel.score         AS score,
               rel.evidence      AS evidence,
               p.id              AS proposal_section_id,
               p.title           AS proposal_section_title
        ORDER BY r.section_path
        """
        with self._driver.session() as session:
            result = session.run(query)
            rows = [dict(record) for record in result]

        logger.info(f"ComplianceMatrixService: Retrieved {len(rows)} compliance mappings.")
        return rows

    def get_missing_requirements(self) -> List[Dict[str, Any]]:
        """
        Find requirements that have NO associated proposal section (gaps).

        Returns:
            List of requirement dicts that are unlinked.
        """
        query = """
        MATCH (r:Requirement)
        WHERE NOT (r)<-[:COMPLIES_WITH]-()
        RETURN r.id           AS requirement_id,
               r.section_path AS section_path,
               r.description  AS description,
               r.is_mandatory AS is_mandatory
        ORDER BY r.is_mandatory DESC, r.section_path
        """
        with self._driver.session() as session:
            result = session.run(query)
            gaps = [dict(record) for record in result]

        logger.info(f"ComplianceMatrixService: Found {len(gaps)} unaddressed requirements.")
        return gaps

    def has_evidence_link(self, requirement_id: str) -> bool:
        """Check if a Requirement node is connected to Evidence via SATISFIED_BY."""
        query = """
        MATCH (r:Requirement {id: $rid})<-[:SATISFIED_BY]-(e:Evidence)
        RETURN e.id AS eid LIMIT 1
        """
        with self._driver.session() as session:
            result = session.run(query, rid=requirement_id)
            return result.single() is not None

    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Return aggregate compliance statistics.

        Returns:
            Dict with total requirements, compliant/partial/non-compliant/missing counts.
        """
        query = """
        MATCH (r:Requirement)
        OPTIONAL MATCH (r)<-[rel:COMPLIES_WITH]-()
        RETURN r.id        AS req_id,
               rel.status  AS status
        """
        with self._driver.session() as session:
            result = session.run(query)
            records = [dict(r) for r in result]

        total = len(records)
        compliant = sum(1 for r in records if r["status"] == "COMPLIANT")
        partial = sum(1 for r in records if r["status"] == "PARTIAL")
        non_compliant = sum(1 for r in records if r["status"] == "NON_COMPLIANT")
        missing = sum(1 for r in records if r["status"] is None)

        summary = {
            "total_requirements": total,
            "compliant": compliant,
            "partial": partial,
            "non_compliant": non_compliant,
            "missing": missing,
            "compliance_rate": round(compliant / total * 100, 1) if total > 0 else 0,
        }
        logger.info(f"ComplianceMatrixService: Summary — {summary}")
        return summary

    def export_to_csv(self, filepath: str = "compliance_matrix.csv") -> str:
        """
        6.1 Build Matrix: Exports the structured table of requirements and 
        their compliance status to a CSV file.
        """
        import csv
        matrix_data = self.get_compliance_matrix()
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Requirement ID", "Section Path", "Mandatory", "Status", "Score", "Proposal Section", "Evidence Ref"])
            for row in matrix_data:
                writer.writerow([
                    row.get("requirement_id", ""),
                    row.get("section_path", ""),
                    "Yes" if row.get("is_mandatory") else "No",
                    row.get("status", "MISSING"),
                    row.get("score", 0.0),
                    row.get("proposal_section_title", ""),
                    row.get("evidence", "")
                ])
                
        logger.info(f"ComplianceMatrixService: Exported matrix to {filepath}")
        return filepath
