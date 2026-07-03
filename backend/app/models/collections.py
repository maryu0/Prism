"""Central list of Mongo collection names — avoids magic strings scattered across modules."""

USERS = "users"
WORKSPACES = "workspaces"
REPOSITORIES = "repositories"
DEVELOPER_PROFILES = "developerProfiles"
LEARNING_PATHS = "learningPaths"
LEARNING_MODULES = "learningModules"
CHAT_SESSIONS = "chatSessions"
CHAT_MESSAGES = "chatMessages"
INGESTION_JOBS = "ingestionJobs"
AUDIT_LOGS = "auditLogs"

# Not part of the original 10-collection schema — a staging area for Phase 3's
# parsed output, consumed by Phase 4 when it writes the actual Neo4j graph.
PARSED_FILES = "parsedFiles"
