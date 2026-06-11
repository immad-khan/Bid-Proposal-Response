// ==============================================================================
// Neo4j Database Schema Initialization
// ==============================================================================

// Create uniqueness constraint on Requirement ID
CREATE CONSTRAINT unique_requirement_id IF NOT EXISTS
FOR (r:Requirement) REQUIRE r.id IS UNIQUE;

// Create index on section paths for quick path queries
CREATE INDEX index_requirement_section IF NOT EXISTS
FOR (r:Requirement) ON (r.section);

// Create uniqueness constraint on ProposalSection ID
CREATE CONSTRAINT unique_proposal_section_id IF NOT EXISTS
FOR (p:ProposalSection) REQUIRE p.id IS UNIQUE;
