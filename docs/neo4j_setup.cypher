CREATE CONSTRAINT inspection_id IF NOT EXISTS
FOR (node:Inspection) REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT category_id IF NOT EXISTS
FOR (node:ProductCategory) REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT evidence_id IF NOT EXISTS
FOR (node:Evidence) REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT support_message_id IF NOT EXISTS
FOR (node:SupportMessage) REQUIRE node.id IS UNIQUE;

CREATE INDEX inspection_created_at IF NOT EXISTS
FOR (node:Inspection) ON (node.created_at);

CREATE INDEX support_message_created_at IF NOT EXISTS
FOR (node:SupportMessage) ON (node.created_at);
