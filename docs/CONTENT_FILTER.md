# Content Filter

ChatMode includes a built-in content filtering system that allows administrators to control inappropriate language and content in conversations. The filter can be configured per-agent and applies to both user-injected messages and agent responses.

---

## Features

- **Three Filter Actions**: Block, Censor, or Warn
- **Per-Agent Configuration**: Each agent can have different filter rules
- **Global Enable/Disable**: Turn filtering on or off system-wide
- **Custom Word Lists**: Define your own blocked words and phrases
- **Custom Messages**: Set custom messages shown when content is blocked
- **Real-time Filtering**: Applies to both user messages and AI responses

---

## Filter Actions

### Block
Rejects the message entirely and displays a filter message instead.

**Example:**
```
User: "This is a badword message"
System: "This message contains inappropriate content and has been blocked."
```

### Censor
Replaces blocked words with asterisks while allowing the message through.

**Example:**
```
User: "This is a badword message"
Result: "This is a ******* message"
```

### Warn
Allows the message but flags it with a warning notice.

**Example:**
```
User: "This is a badword message"
System: "Warning: Content flagged for containing: badword"
```

---

## Configuration

### Via Web Admin (Agent Manager)

1. Navigate to the **Agent Manager** tab
2. Click **Create Agent** or **Edit** an existing agent
3. Scroll to the **Content Filter Settings** section
4. Configure the following options:

| Setting | Description | Default |
|---------|-------------|---------|
| **Enable Content Filter** | Master on/off switch for filtering | Enabled |
| **Blocked Words/Phrases** | Comma-separated list of words to filter | Empty |
| **Filter Action** | How to handle violations (block/censor/warn) | Block |
| **Filter Message** | Message shown when content is blocked | "This message contains inappropriate content..." |

### Example Configuration

**Strict Filter (Block):**
```
Enable Content Filter: ☑
Blocked Words: badword1, badword2, inappropriate phrase, another word
Filter Action: Block
Filter Message: This content violates our community guidelines and has been blocked.
```

**Moderate Filter (Censor):**
```
Enable Content Filter: ☑
Blocked Words: profanity1, profanity2
Filter Action: Censor
Filter Message: N/A (content is censored, not blocked)
```

**Lenient Filter (Warn):**
```
Enable Content Filter: ☑
Blocked Words: mildword1, mildword2
Filter Action: Warn
Filter Message: Please keep conversations respectful.
```

---

## API Endpoints

### Update Agent Filter Settings

```bash
PUT /api/v1/agents/{agent_id}/permissions
Content-Type: application/json
Authorization: Bearer {token}

{
  "filter_enabled": true,
  "blocked_words": ["badword1", "badword2"],
  "filter_action": "block",
  "filter_message": "Content blocked due to inappropriate language."
}
```

### Reload Filter from Database

```bash
POST /filter/reload
```

This reloads the content filter settings from the database without restarting the server.

---

## Database Schema

Filter settings are stored in the `agent_permissions` table:

```sql
CREATE TABLE agent_permissions (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    filter_enabled BOOLEAN DEFAULT TRUE,
    blocked_words JSON DEFAULT '[]',
    filter_action VARCHAR(20) DEFAULT 'block',
    filter_message TEXT DEFAULT 'This message contains inappropriate content...',
    -- ... other permission fields
);
```

---

## Default State

**The content filter is OFF by default.** No filtering occurs unless explicitly enabled.

To enable filtering:
1. Go to **Agent Manager** tab
2. Edit an agent and check "Enable Content Filter"
3. Add your blocked words list
4. Or use the global toggle in Session Control tab

This ensures users have full control over when and how filtering is applied.

---

## Best Practices

### Word List Management

1. **Start Conservative**: Begin with a small list and expand as needed
2. **Use Phrases**: Block multi-word phrases, not just single words
3. **Case Insensitive**: The filter is case-insensitive by default
4. **Review Regularly**: Update word lists based on community needs
5. **Context Matters**: Consider using "warn" instead of "block" for edge cases

### Action Selection

| Action | Best For | User Experience |
|--------|----------|-----------------|
| **Block** | Strict moderation, educational environments | Clear boundaries |
| **Censor** | Adult-friendly spaces, creative writing | Content flows with masking |
| **Warn** | Self-moderated communities, mature audiences | Freedom with accountability |

### Performance

- Filter checks add minimal latency (~1-2ms per message)
- Word lists are compiled into efficient regex patterns
- Filter runs in the same thread as message processing

---

## Troubleshooting

### Filter Not Working

1. Check that `filter_enabled` is `true` in the agent permissions
2. Verify the word list is not empty
3. Reload the filter: `POST /filter/reload`
4. Check server logs for filter initialization messages

### Too Many False Positives

1. Switch from "block" to "warn" action
2. Review and refine your word list
3. Remove words that appear in legitimate contexts

### Filter Too Permissive

1. Add more specific words and phrases
2. Switch from "warn" to "censor" or "block"
3. Review agent responses for edge cases

---

## Integration with Other Systems

The content filter integrates with:

- **Audit Logging**: All filter actions are logged with user context
- **Session Management**: Filter applies to all messages in a session
- **Memory System**: Filtered messages are still stored in conversation history
- **TTS System**: Blocked messages don't generate audio

---

*See also: [Agent Management](./AGENTS.md) | [API Reference](./API.md) | [Security](./SECURITY.md)*
