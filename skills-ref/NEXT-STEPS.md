# Next Steps - What Linus Would Approve

> "Talk is cheap. Show me the code."

## Current State (Honest Assessment)

**What works:**
- 45 skill definitions with type composition
- Auth capability checking (tested with real HubSpot)
- 84 tests passing

**What doesn't work yet:**
- Skills are DEFINITIONS, not IMPLEMENTATIONS
- Can't actually RUN `hubspot-read → deal-analysis`
- 160+ scripts exist but aren't wrapped
- No CLI to execute skill chains

## Priority 1: Make It Actually Run

The #1 problem: we have a type system but no runtime.

```bash
# This should work but doesn't:
skills run hubspot-deals deal-analysis

# Instead we have to manually:
python3 scripts/api/hubspot/get_deals.py | python3 scripts/analysis/analyze_deals.py
```

**Action:** Create a minimal skill runner that:
1. Checks auth (we have this)
2. Validates composition (we have this)
3. Actually executes the skill (we DON'T have this)
4. Pipes output to next skill

Don't over-engineer. Start with 3 skills that work end-to-end.

## Priority 2: Wrap Real Scripts (Not Abstractions)

We have 175 scripts. Wrap the ones that WORK, don't create new abstractions.

**Tier 1 - Ready to wrap (have auth, tested):**
```
hubspot-read     → scripts/api/hubspot/get_companies.py (WORKS)
hubspot-deals    → scripts/api/hubspot/get_deals.py (WORKS)
slack-read       → scripts/integrations/slack/search_slack_messages.py (WORKS)
fireflies-read   → scripts/api/fireflies/get_transcripts.py (WORKS)
perplexity       → scripts/integrations/perplexity/perplexity_search.py (WORKS)
```

**Tier 2 - Need auth setup:**
```
gmail-read       → scripts/integrations/gmail/ (needs OAuth pickle)
outlook-read     → scripts/api/outlook/ (needs MSAL cache)
gdrive-read      → scripts/integrations/gdrive/ (needs OAuth pickle)
```

**Don't wrap yet:**
- Scripts that don't work
- Scripts that need refactoring
- Theoretical skills nobody uses

## Priority 3: Test Auth Flows End-to-End

We checked token EXISTENCE, not token VALIDITY.

```python
# Current: checks if file exists
token_file.exists()  # True

# Need: checks if token actually works
requests.get(api_url, headers=auth).status_code == 200
```

**Action:** For each auth type, add a "ping" test:
- `env-token`: Make one API call, check 200
- `oauth-google`: Try to refresh, check valid
- `oauth-msal`: Try to get access token, check not expired

## Priority 4: Fix the Broken Auth

Current status shows these are broken:
```
✗ gmail-personal: Token not found (run OAuth flow)
✗ outlook: Token cache not found (run device flow)
✗ godaddy: Missing GODADDY_API_SECRET
✗ linear: Missing LINEAR_API_TOKEN
✗ asana: Missing ASANA_TOKEN
```

**Don't add more skills until these work.** Fix auth first.

## What NOT To Do (Linus Anti-Patterns)

1. **Don't add more abstractions**
   - No "skill registry service"
   - No "auth provider factory"
   - No "composition middleware"

2. **Don't write more definitions without implementations**
   - Every skill definition should have a working script
   - If the script doesn't exist, don't define the skill

3. **Don't test with mocks**
   - Real HubSpot API, not mock responses
   - Real Slack messages, not fixtures
   - Real auth tokens, not test tokens

4. **Don't over-document**
   - Code is the documentation
   - If it needs a doc, simplify the code

## Concrete Next Actions

### This Week
1. Create `skills run` CLI that executes ONE skill with real auth
2. Wrap `hubspot-deals` as the first fully-working skill
3. Add auth "ping" tests that hit real APIs

### Next Week
1. Add `hubspot-read`, `slack-read`, `fireflies-read`
2. Create first working chain: `hubspot-deals → deal-analysis`
3. Fix Gmail OAuth (most valuable missing auth)

### Later (only if above works)
1. Wrap remaining Tier 1 scripts
2. Add composition runtime for multi-skill chains
3. Consider upstream PR to agentskills/agentskills

## Success Criteria

A skill is "done" when:
```bash
# This actually runs and returns real data:
skills run hubspot-deals --limit 10

# This actually chains and produces output:
skills chain "hubspot-deals | deal-analysis" --format json
```

Not when:
- Tests pass with mocks
- Type definitions compile
- Documentation exists

---

> "I'm a huge proponent of designing your code around the data,
> rather than the other way around."
> — Linus Torvalds

The data is: API responses from HubSpot, Slack, Gmail.
The code should: fetch it, transform it, chain it.
Everything else is noise.
