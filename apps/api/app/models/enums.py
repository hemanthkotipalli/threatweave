from enum import Enum


class Severity(str, Enum):
    """
    5-tier incident and finding severity classification system.
    """
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Modality(str, Enum):
    """
    Modality type classification for threat intelligence inputs.
    """
    TEXT = "text"
    URL = "url"
    QR = "qr"
    IMAGE = "image"
    VOICE = "voice"

class AgentStatus(str, Enum):
    """
    Swarm agent run execution status flags.
    """
    SKIPPED = "skipped"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class FindingStatus(str, Enum):
    """
    Swarm agent consensus finding confirmation status.
    """
    OK = "ok"
    DEGRADED_FALLBACK = "degraded_fallback"
    FAILED = "failed"
    SKIPPED = "skipped"

class SourceType(str, Enum):
    """
    RAG lookup source classification options.
    """
    CERT_IN = "CERT-In"
    RBI = "RBI"
    SCAM_INTEL = "Scam-Intel"
