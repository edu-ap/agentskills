"""
Skill Catalog with Composition and Auth Metadata

Defines composition types for a comprehensive skill system demonstrating
real-world integrations across email, messaging, CRM, calendar, and more.

Type Philosophy (Unix-inspired):
- No arbitrary levels - just type compatibility
- Skills declare what they produce and consume
- Any skill can chain to any other if types match

Auth Philosophy (Linus/Carmack/Hotz):
- Auth is a capability, not a skill
- Skills declare what auth they NEED, not how to get it
- Check auth BEFORE composition validation
- Fail fast with clear errors
"""

from dataclasses import dataclass, field
from typing import Optional

# Import auth capabilities (when available)
try:
    from auth_capabilities import check_skill_auth, get_capability
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    def check_skill_auth(name, services):
        return True, f"{name}: Auth check skipped (module not available)"


# ============================================================
# COMPOSITION TYPE DEFINITIONS
# ============================================================

COMPOSITION_TYPES = {
    # === Communication Types ===
    "email-list": "List of emails with id, subject, from, date, snippet, source",
    "message-list": "List of messages with ts, user, text, channel, source",
    "thread-data": "Thread/conversation with replies and participants",

    # === CRM Types ===
    "crm-companies": "List of companies with id, name, domain, properties",
    "crm-contacts": "List of contacts with id, name, email, company, properties",
    "crm-deals": "List of deals with id, name, stage, amount, close_date",
    "crm-activities": "List of CRM activities (calls, emails, meetings)",

    # === Calendar Types ===
    "calendar-events": "List of calendar events with title, time, attendees, location",
    "meeting-details": "Single meeting with full details and agenda",

    # === Meeting/Transcript Types ===
    "transcript-list": "List of meeting transcripts with id, title, date, participants",
    "transcript-data": "Full transcript with speakers, timestamps, and text",

    # === Search/Research Types ===
    "search-results": "Web search results with urls, titles, snippets, sources",
    "research-findings": "Synthesised research with sources and conclusions",

    # === Task/Issue Types ===
    "task-list": "List of tasks with id, title, status, assignee, due_date",
    "issue-list": "List of issues/tickets with id, title, status, priority",

    # === File Types ===
    "file-list": "List of files with id, name, path, modified_date, size",
    "file-content": "File content with metadata",

    # === Code/Repository Types ===
    "pr-list": "List of pull requests with id, title, status, author",
    "commit-list": "List of commits with id, message, author, date",
    "repo-data": "Repository information with branches, stats",

    # === Aggregated/Intelligence Types ===
    "intel-brief": "Aggregated intelligence summary with timeline and alerts",
    "prep-brief": "Preparation brief with context, agenda, and action items",
    "action-items": "Extracted action items with owners and deadlines",
    "status-report": "Status report with metrics, progress, and blockers",

    # === Workflow Types ===
    "workflow-list": "List of workflow executions with id, status, timestamps",
    "workflow-data": "Workflow execution details with inputs and outputs",

    # === Writer Input Types ===
    "draft-request": "Email draft specification with recipient, subject, body",
    "message-content": "Message content with channel/recipient and text",
    "document-spec": "Document generation specification with template and data",
    "task-spec": "Task creation specification with title, description, assignee",

    # === Writer Output Types ===
    "draft-result": "Created draft with id and preview",
    "send-result": "Message send confirmation with timestamp and id",
    "document-file": "Generated document file path and metadata",
    "task-result": "Created task with id and link",
}


@dataclass
class SkillDefinition:
    """Definition of a skill with composition metadata."""

    name: str
    description: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    operation: str = "READ"  # READ or WRITE
    services: list[str] = field(default_factory=list)

    def check_auth(self) -> tuple[bool, str]:
        """Check if required auth capabilities are available."""
        return check_skill_auth(self.name, self.services)

    def to_frontmatter(self) -> str:
        """Generate YAML frontmatter for SKILL.md."""
        lines = [
            "---",
            f"name: {self.name}",
            f"description: {self.description}",
        ]

        if self.inputs or self.outputs:
            lines.append("composition:")
            if self.inputs:
                lines.append("  inputs:")
                for inp in self.inputs:
                    lines.append(f"    - {inp}")
            if self.outputs:
                lines.append("  outputs:")
                for out in self.outputs:
                    lines.append(f"    - {out}")

        if self.services:
            lines.append("auth:")
            lines.append("  services:")
            for svc in self.services:
                lines.append(f"    - {svc}")

        lines.append("---")
        return "\n".join(lines)


# ============================================================
# ATOMIC SKILLS - Email & Messaging
# ============================================================

EMAIL_SKILLS = {
    "email-read": SkillDefinition(
        name="email-read",
        description="Search and fetch emails from Gmail or Outlook",
        inputs=[],
        outputs=["email-list"],
        operation="READ",
        services=["gmail", "outlook"],
    ),
    "email-draft": SkillDefinition(
        name="email-draft",
        description="Create email drafts in Gmail or Outlook",
        inputs=["draft-request"],
        outputs=["draft-result"],
        operation="WRITE",
        services=["gmail", "outlook"],
    ),
    "email-send": SkillDefinition(
        name="email-send",
        description="Send emails via Gmail or Outlook",
        inputs=["draft-request"],
        outputs=["send-result"],
        operation="WRITE",
        services=["gmail", "outlook"],
    ),
}

MESSAGING_SKILLS = {
    "slack-read": SkillDefinition(
        name="slack-read",
        description="Search and fetch messages from Slack channels",
        inputs=[],
        outputs=["message-list"],
        operation="READ",
        services=["slack"],
    ),
    "slack-write": SkillDefinition(
        name="slack-write",
        description="Post messages to Slack channels",
        inputs=["message-content"],
        outputs=["send-result"],
        operation="WRITE",
        services=["slack"],
    ),
    "teams-read": SkillDefinition(
        name="teams-read",
        description="Search and fetch messages from Microsoft Teams",
        inputs=[],
        outputs=["message-list"],
        operation="READ",
        services=["teams"],
    ),
}

# ============================================================
# ATOMIC SKILLS - CRM (HubSpot, Salesforce)
# ============================================================

CRM_SKILLS = {
    "hubspot-read": SkillDefinition(
        name="hubspot-read",
        description="Fetch combined CRM data from HubSpot (companies, contacts, deals)",
        inputs=[],
        outputs=["crm-companies", "crm-contacts", "crm-deals", "crm-activities"],
        operation="READ",
        services=["hubspot"],
    ),
    "hubspot-companies": SkillDefinition(
        name="hubspot-companies",
        description="Fetch companies from HubSpot CRM",
        inputs=[],
        outputs=["crm-companies"],
        operation="READ",
        services=["hubspot"],
    ),
    "hubspot-contacts": SkillDefinition(
        name="hubspot-contacts",
        description="Fetch contacts from HubSpot CRM",
        inputs=[],
        outputs=["crm-contacts"],
        operation="READ",
        services=["hubspot"],
    ),
    "hubspot-deals": SkillDefinition(
        name="hubspot-deals",
        description="Fetch deals and pipeline data from HubSpot",
        inputs=[],
        outputs=["crm-deals"],
        operation="READ",
        services=["hubspot"],
    ),
    "hubspot-activities": SkillDefinition(
        name="hubspot-activities",
        description="Fetch engagement activities from HubSpot",
        inputs=[],
        outputs=["crm-activities"],
        operation="READ",
        services=["hubspot"],
    ),
}

# ============================================================
# ATOMIC SKILLS - Calendar & Meetings
# ============================================================

CALENDAR_SKILLS = {
    "calendar-read": SkillDefinition(
        name="calendar-read",
        description="Fetch calendar events from Google or Outlook",
        inputs=[],
        outputs=["calendar-events"],
        operation="READ",
        services=["google-calendar", "outlook-calendar"],
    ),
    "transcript-list": SkillDefinition(
        name="transcript-list",
        description="List meeting transcripts from Fireflies or similar",
        inputs=[],
        outputs=["transcript-list"],
        operation="READ",
        services=["fireflies", "otter"],
    ),
    "transcript-read": SkillDefinition(
        name="transcript-read",
        description="Fetch full meeting transcript content",
        inputs=[],
        outputs=["transcript-data"],
        operation="READ",
        services=["fireflies", "otter"],
    ),
}

# ============================================================
# ATOMIC SKILLS - Search & Research
# ============================================================

SEARCH_SKILLS = {
    "web-search": SkillDefinition(
        name="web-search",
        description="Search the web using Perplexity or similar",
        inputs=[],
        outputs=["search-results"],
        operation="READ",
        services=["perplexity", "tavily", "serper"],
    ),
    "wayback-read": SkillDefinition(
        name="wayback-read",
        description="Fetch historical web pages from Wayback Machine",
        inputs=[],
        outputs=["file-content"],
        operation="READ",
        services=["wayback"],
    ),
}

# ============================================================
# ATOMIC SKILLS - Task & Issue Tracking
# ============================================================

TASK_SKILLS = {
    "asana-read": SkillDefinition(
        name="asana-read",
        description="Fetch tasks from Asana projects",
        inputs=[],
        outputs=["task-list"],
        operation="READ",
        services=["asana"],
    ),
    "asana-write": SkillDefinition(
        name="asana-write",
        description="Create tasks in Asana",
        inputs=["task-spec"],
        outputs=["task-result"],
        operation="WRITE",
        services=["asana"],
    ),
    "linear-read": SkillDefinition(
        name="linear-read",
        description="Fetch issues from Linear",
        inputs=[],
        outputs=["issue-list"],
        operation="READ",
        services=["linear"],
    ),
    "github-issues": SkillDefinition(
        name="github-issues",
        description="Fetch issues from GitHub repositories",
        inputs=[],
        outputs=["issue-list"],
        operation="READ",
        services=["github"],
    ),
    "github-prs": SkillDefinition(
        name="github-prs",
        description="Fetch pull requests from GitHub repositories",
        inputs=[],
        outputs=["pr-list"],
        operation="READ",
        services=["github"],
    ),
}

# ============================================================
# ATOMIC SKILLS - File Storage
# ============================================================

FILE_SKILLS = {
    "gdrive-read": SkillDefinition(
        name="gdrive-read",
        description="List and fetch files from Google Drive",
        inputs=[],
        outputs=["file-list"],
        operation="READ",
        services=["google-drive"],
    ),
    "sharepoint-read": SkillDefinition(
        name="sharepoint-read",
        description="List and fetch files from SharePoint",
        inputs=[],
        outputs=["file-list"],
        operation="READ",
        services=["sharepoint"],
    ),
    "dropbox-read": SkillDefinition(
        name="dropbox-read",
        description="List and fetch files from Dropbox",
        inputs=[],
        outputs=["file-list"],
        operation="READ",
        services=["dropbox"],
    ),
}

# ============================================================
# ATOMIC SKILLS - Workflow Automation
# ============================================================

AUTOMATION_SKILLS = {
    "n8n-read": SkillDefinition(
        name="n8n-read",
        description="Query n8n workflow executions and data",
        inputs=[],
        outputs=["workflow-data"],
        operation="READ",
        services=["n8n"],
    ),
}

# ============================================================
# ATOMIC SKILLS - Document Generation
# ============================================================

DOCUMENT_SKILLS = {
    "pdf-generate": SkillDefinition(
        name="pdf-generate",
        description="Generate PDF documents from content",
        inputs=["document-spec"],
        outputs=["document-file"],
        operation="WRITE",
        services=["local"],
    ),
    "docx-generate": SkillDefinition(
        name="docx-generate",
        description="Generate Word documents from templates",
        inputs=["document-spec"],
        outputs=["document-file"],
        operation="WRITE",
        services=["local"],
    ),
}

# ============================================================
# COMPOSITE SKILLS - Intelligence & Analysis
# ============================================================

INTEL_SKILLS = {
    "customer-intel": SkillDefinition(
        name="customer-intel",
        description="Aggregate customer intelligence from CRM, email, and messaging",
        inputs=["email-list", "message-list", "crm-companies", "crm-contacts", "crm-deals", "crm-activities"],
        outputs=["intel-brief"],
        operation="READ",
        services=["hubspot", "slack", "gmail", "outlook"],
    ),
    "deal-analysis": SkillDefinition(
        name="deal-analysis",
        description="Analyse deal pipeline and identify risks",
        inputs=["crm-deals", "crm-activities"],
        outputs=["intel-brief"],
        operation="READ",
        services=["hubspot"],
    ),
    "deal-loss-analysis": SkillDefinition(
        name="deal-loss-analysis",
        description="Analyse lost deals to identify patterns and improvement areas",
        inputs=["crm-deals", "crm-activities", "email-list"],
        outputs=["intel-brief", "research-findings"],
        operation="READ",
        services=["hubspot"],
    ),
    "competitor-intel": SkillDefinition(
        name="competitor-intel",
        description="Research competitor information from web and CRM",
        inputs=["search-results", "crm-companies"],
        outputs=["intel-brief"],
        operation="READ",
        services=["perplexity", "hubspot"],
    ),
}

# ============================================================
# COMPOSITE SKILLS - Meeting & Preparation
# ============================================================

MEETING_SKILLS = {
    "meeting-prep": SkillDefinition(
        name="meeting-prep",
        description="Prepare briefing for upcoming meetings",
        inputs=["calendar-events", "email-list", "message-list", "crm-companies"],
        outputs=["prep-brief"],
        operation="READ",
        services=["calendar", "gmail", "slack", "hubspot"],
    ),
    "meeting-summary": SkillDefinition(
        name="meeting-summary",
        description="Summarise meeting from transcript",
        inputs=["transcript-data"],
        outputs=["intel-brief", "action-items"],
        operation="READ",
        services=["fireflies"],
    ),
    "meeting-followup": SkillDefinition(
        name="meeting-followup",
        description="Generate follow-up actions from meeting",
        inputs=["transcript-data", "action-items"],
        outputs=["draft-request", "task-spec"],
        operation="READ",
        services=["fireflies"],
    ),
}

# ============================================================
# COMPOSITE SKILLS - Research & Synthesis
# ============================================================

RESEARCH_SKILLS = {
    "research": SkillDefinition(
        name="research",
        description="Research a topic using web search and synthesise findings",
        inputs=["search-results"],
        outputs=["research-findings"],
        operation="READ",
        services=["perplexity", "tavily"],
    ),
    "deep-research": SkillDefinition(
        name="deep-research",
        description="Comprehensive multi-source research with synthesis",
        inputs=["search-results", "file-content"],
        outputs=["research-findings"],
        operation="READ",
        services=["perplexity", "tavily"],
    ),
    "company-research": SkillDefinition(
        name="company-research",
        description="Research a company using web and CRM data",
        inputs=["search-results", "crm-companies"],
        outputs=["research-findings"],
        operation="READ",
        services=["perplexity", "hubspot"],
    ),
}

# ============================================================
# COMPOSITE SKILLS - Communication
# ============================================================

COMMUNICATION_SKILLS = {
    "smart-reply": SkillDefinition(
        name="smart-reply",
        description="Generate contextual email replies",
        inputs=["email-list", "thread-data"],
        outputs=["draft-request"],
        operation="READ",
        services=["gmail", "outlook"],
    ),
    "email-compose": SkillDefinition(
        name="email-compose",
        description="Compose emails with context from CRM and history",
        inputs=["email-list", "crm-contacts"],
        outputs=["draft-result"],
        operation="WRITE",
        services=["gmail", "outlook", "hubspot"],
    ),
}

# ============================================================
# WORKFLOW SKILLS - Daily Operations
# ============================================================

DAILY_SKILLS = {
    "morning-briefing": SkillDefinition(
        name="morning-briefing",
        description="Generate morning briefing with calendar, tasks, and priorities",
        inputs=["calendar-events", "task-list", "action-items"],
        outputs=["prep-brief"],
        operation="READ",
        services=["calendar", "asana"],
    ),
    "daily-digest": SkillDefinition(
        name="daily-digest",
        description="Generate daily digest of emails, messages, and tasks",
        inputs=["email-list", "message-list", "task-list", "calendar-events"],
        outputs=["prep-brief"],
        operation="READ",
        services=["gmail", "slack", "asana", "calendar"],
    ),
    "daily-synthesis": SkillDefinition(
        name="daily-synthesis",
        description="Synthesise daily activities and extract action items",
        inputs=["email-list", "message-list"],
        outputs=["action-items", "prep-brief"],
        operation="READ",
        services=["gmail", "slack"],
    ),
    "action-extraction": SkillDefinition(
        name="action-extraction",
        description="Extract action items from emails and messages",
        inputs=["email-list", "message-list"],
        outputs=["action-items"],
        operation="READ",
        services=["gmail", "slack"],
    ),
    "weekly-review": SkillDefinition(
        name="weekly-review",
        description="Generate weekly status review",
        inputs=["action-items", "crm-deals", "task-list"],
        outputs=["status-report"],
        operation="READ",
        services=["hubspot", "asana"],
    ),
}

# ============================================================
# WORKFLOW SKILLS - Project Management
# ============================================================

PROJECT_SKILLS = {
    "project-status": SkillDefinition(
        name="project-status",
        description="Aggregate project status from multiple sources",
        inputs=["task-list", "issue-list", "pr-list"],
        outputs=["status-report"],
        operation="READ",
        services=["asana", "linear", "github"],
    ),
    "sprint-report": SkillDefinition(
        name="sprint-report",
        description="Generate sprint report from issues and PRs",
        inputs=["issue-list", "pr-list", "commit-list"],
        outputs=["status-report"],
        operation="READ",
        services=["linear", "github"],
    ),
}

# ============================================================
# ALL SKILLS REGISTRY
# ============================================================

ATOMIC_SKILLS = {
    **EMAIL_SKILLS,
    **MESSAGING_SKILLS,
    **CRM_SKILLS,
    **CALENDAR_SKILLS,
    **SEARCH_SKILLS,
    **TASK_SKILLS,
    **FILE_SKILLS,
    **AUTOMATION_SKILLS,
    **DOCUMENT_SKILLS,
}

COMPOSITE_SKILLS = {
    **INTEL_SKILLS,
    **MEETING_SKILLS,
    **RESEARCH_SKILLS,
    **COMMUNICATION_SKILLS,
    **DAILY_SKILLS,
    **PROJECT_SKILLS,
}

ALL_SKILLS = {**ATOMIC_SKILLS, **COMPOSITE_SKILLS}


def get_skill(name: str) -> Optional[SkillDefinition]:
    """Get skill definition by name."""
    return ALL_SKILLS.get(name)


def get_skills_by_output(output_type: str) -> list[SkillDefinition]:
    """Find all skills that produce a given output type."""
    return [s for s in ALL_SKILLS.values() if output_type in s.outputs]


def get_skills_by_input(input_type: str) -> list[SkillDefinition]:
    """Find all skills that consume a given input type."""
    return [s for s in ALL_SKILLS.values() if input_type in s.inputs]


def can_compose(source_name: str, target_name: str) -> tuple[bool, str]:
    """Check if source skill can compose into target skill."""
    source = get_skill(source_name)
    target = get_skill(target_name)

    if not source:
        return False, f"Unknown skill: {source_name}"
    if not target:
        return False, f"Unknown skill: {target_name}"

    if not source.outputs:
        return False, f"{source_name} produces no outputs"
    if not target.inputs:
        return True, f"{target_name} accepts any input (unconstrained)"

    for output in source.outputs:
        if output in target.inputs:
            return True, f"Type match: {source_name} outputs '{output}' which {target_name} accepts"

    return False, (
        f"Type mismatch: {source_name} outputs {source.outputs} "
        f"but {target_name} expects {target.inputs}"
    )


def validate_chain(skill_names: list[str]) -> tuple[bool, list[str]]:
    """Validate a chain of skills can compose together."""
    if len(skill_names) < 2:
        return True, ["Single skill - no composition needed"]

    messages = []
    all_valid = True

    for i in range(len(skill_names) - 1):
        source = skill_names[i]
        target = skill_names[i + 1]
        valid, reason = can_compose(source, target)

        status = "✓" if valid else "✗"
        messages.append(f"{status} {source} → {target}: {reason}")

        if not valid:
            all_valid = False

    return all_valid, messages


def validate_chain_with_auth(skill_names: list[str]) -> tuple[bool, list[str]]:
    """
    Validate composition AND auth for a skill chain.
    Checks auth FIRST (fail fast), then type composition.
    """
    messages = []
    all_valid = True

    # Phase 1: Auth check (fail fast)
    for name in skill_names:
        skill = get_skill(name)
        if not skill:
            messages.append(f"✗ {name}: Unknown skill")
            all_valid = False
            continue

        auth_valid, auth_msg = skill.check_auth()
        if not auth_valid:
            messages.append(f"✗ {name}: {auth_msg}")
            all_valid = False
        else:
            messages.append(f"✓ {name}: {auth_msg}")

    if not all_valid:
        messages.append("--- Auth check FAILED, skipping composition ---")
        return False, messages

    messages.append("--- Auth OK, checking composition ---")

    # Phase 2: Composition check
    comp_valid, comp_msgs = validate_chain(skill_names)
    messages.extend(comp_msgs)

    return comp_valid, messages


def check_all_auth() -> dict[str, tuple[bool, str]]:
    """Check auth status for all skills."""
    results = {}
    for name, skill in ALL_SKILLS.items():
        valid, msg = skill.check_auth()
        results[name] = (valid, msg)
    return results


if __name__ == "__main__":
    print("=== SKILL CATALOG ===\n")
    print(f"Total skills: {len(ALL_SKILLS)}")
    print(f"  Atomic: {len(ATOMIC_SKILLS)}")
    print(f"  Composite: {len(COMPOSITE_SKILLS)}")
    print(f"Composition types: {len(COMPOSITION_TYPES)}")

    print("\n=== COMPOSITION EXAMPLES ===\n")

    chains = [
        ["email-read", "customer-intel"],
        ["hubspot-deals", "deal-analysis"],
        ["web-search", "deep-research"],
        ["transcript-read", "meeting-summary"],
        ["calendar-read", "meeting-prep"],
        ["email-read", "action-extraction"],
        ["github-issues", "project-status"],
    ]

    for chain in chains:
        valid, messages = validate_chain(chain)
        status = "✓" if valid else "✗"
        print(f"{status} {' → '.join(chain)}")
