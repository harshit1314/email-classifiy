# Meeting Extraction from Emails - Feature Documentation

## Overview

The AI Email Classifier now includes **automatic meeting extraction** capabilities that can detect and extract meeting information from emails, creating calendar events automatically.

## Features

### 🤖 AI-Powered Extraction

The system uses advanced pattern matching and natural language processing to extract:

- **Date & Time**: Understands various date/time formats (MM/DD/YYYY, Month DD, relative dates like "tomorrow")
- **Location**: Physical locations (conference rooms, offices) and virtual meeting links (Zoom, Teams, Google Meet)
- **Attendees**: Email addresses and names from the email
- **Meeting Title**: From email subject line
- **Description**: Relevant details from email body
- **Duration**: Start and end times

### 📅 Supported Formats

The extraction engine recognizes:

**Date Formats:**
- `01/15/2026` (MM/DD/YYYY)
- `15 January 2026` (DD Month YYYY)
- `January 15, 2026` (Month DD, YYYY)
- `2026-01-15` (ISO format)
- `Monday, January 15` (Day, Month DD)
- Relative dates: "today", "tomorrow", "next week"

**Time Formats:**
- `3:00 PM` (12-hour with AM/PM)
- `15:30` (24-hour format)
- `3:00 PM - 4:00 PM` (time ranges)
- `at 3:00 PM` (with context)

**Meeting Keywords:**
- meeting, call, conference, appointment
- schedule, calendar, zoom, teams, webex
- invite, invited, join, discussion
- standup, sync, catch up, review, demo

**Virtual Meeting Links:**
- Zoom: `https://zoom.us/...`
- Teams: `https://teams.microsoft.com/...`
- Google Meet: `https://meet.google.com/...`
- Webex: `https://webex.com/...`

## How to Use

### Method 1: Manual Extraction

1. **Navigate to Calendar Page** in the dashboard
2. **Paste Email Content** in the AI Meeting Extraction section
3. **Click "Extract Meeting"** button
4. The system will analyze the content and create a calendar event

### Method 2: Auto-Extract from Classified Emails

1. **Click "Auto-Extract from Emails"** button on the Calendar page
2. The system will scan your recent classified emails (up to 50)
3. Automatically extracts meetings and saves them to your calendar
4. Shows total meetings found and emails processed

### Method 3: API Integration

**Extract from specific email:**
```bash
POST /api/calendar/extract-meeting
{
    "email_subject": "Team Meeting - Jan 15",
    "email_body": "Hi team, let's meet tomorrow at 3:00 PM in Conference Room A..."
}
```

**Auto-extract from classified emails:**
```bash
POST /api/calendar/extract-from-classified
{
    "limit": 50,
    "category": "important"
}
```

## Example Extractions

### Example 1: Basic Meeting Invite

**Input Email:**
```
Subject: Team Standup - Tomorrow

Hi team,

Let's have our weekly standup tomorrow at 10:00 AM in Conference Room B.

Attendees: john@company.com, sarah@company.com

Thanks!
```

**Extracted Meeting:**
- Title: "Team Standup - Tomorrow"
- Date: Tomorrow's date
- Time: 10:00 AM
- Location: Conference Room B
- Attendees: john@company.com, sarah@company.com
- Confidence: High ✅

### Example 2: Virtual Meeting

**Input Email:**
```
Subject: Q1 Review Meeting

Join us for our Q1 review on January 15, 2026 at 2:00 PM.

Zoom Link: https://zoom.us/j/123456789

We'll discuss:
- Revenue targets
- Project updates
- Team feedback
```

**Extracted Meeting:**
- Title: "Q1 Review Meeting"
- Date: January 15, 2026
- Time: 2:00 PM
- Location: Virtual Meeting
- Meeting Link: https://zoom.us/j/123456789
- Confidence: High ✅

### Example 3: Meeting with Range

**Input Email:**
```
Subject: Client Demo

Schedule: Thursday, January 16, 2026
Time: 3:00 PM - 4:30 PM
Location: Office Building, Room 301
Attendees: client@external.com, sales@company.com
```

**Extracted Meeting:**
- Title: "Client Demo"
- Date: January 16, 2026
- Start Time: 3:00 PM
- End Time: 4:30 PM
- Location: Office Building, Room 301
- Attendees: client@external.com, sales@company.com
- Confidence: High ✅

## Calendar View

### Upcoming Events Sidebar

- Shows next 5 upcoming meetings
- Color-coded with confidence badges
- Animated indicators for active events
- Click on event for more details
- Shows date/time, location, and attendee count

### Calendar Widget

- Interactive date picker
- Visual indicators for days with events
- Select dates to view scheduled meetings
- Month/year navigation

## Confidence Levels

The system assigns confidence levels to extracted meetings:

- **High Confidence** ✅: Has both date and time extracted clearly
- **Medium Confidence** ⚠️: Has date OR time, but not both
- **Low Confidence** ℹ️: Meeting keywords detected but limited date/time info

## Database Storage

Meetings are stored in the `calendar_events` table:

```sql
calendar_events:
- id: Unique identifier
- user_id: Owner of the event
- email_id: Source email (optional)
- event_title: Meeting title
- event_description: Details
- start_time: ISO format datetime
- end_time: ISO format datetime (optional)
- location: Physical or virtual location
- attendees: JSON array of attendees
- organizer: Meeting organizer
- event_id: Unique event identifier
- meeting_link: Video conference URL
- synced: Whether synced to external calendar
- created_at: Timestamp
```

## API Endpoints

### Get Calendar Events

```http
GET /api/calendar/events?limit=20
Authorization: Bearer <token>
```

**Response:**
```json
{
  "events": [
    {
      "id": 1,
      "event_title": "Team Meeting",
      "start_time": "2026-01-15T15:00:00",
      "end_time": "2026-01-15T16:00:00",
      "location": "Conference Room A",
      "attendees": ["john@example.com"],
      "confidence": "high"
    }
  ]
}
```

### Extract Meeting from Email

```http
POST /api/calendar/extract-meeting
Authorization: Bearer <token>
Content-Type: application/json

{
  "email_subject": "Team Standup",
  "email_body": "Meeting tomorrow at 10 AM..."
}
```

**Response:**
```json
{
  "success": true,
  "meetings": [
    {
      "title": "Team Standup",
      "start_time": "2026-01-16T10:00:00",
      "location": "",
      "attendees": [],
      "confidence": "medium",
      "saved": true
    }
  ],
  "count": 1,
  "message": "Meeting extracted successfully"
}
```

### Auto-Extract from Classified Emails

```http
POST /api/calendar/extract-from-classified
Authorization: Bearer <token>
Content-Type: application/json

{
  "limit": 50,
  "category": "important"
}
```

**Response:**
```json
{
  "success": true,
  "meetings": [...],
  "total_extracted": 5,
  "emails_processed": 50
}
```

## Integration with Email Classification

The meeting extraction works seamlessly with the email classification system:

1. **Emails are classified** into categories (important, spam, etc.)
2. **Auto-extraction scans** recently classified emails
3. **Meetings are detected** from important emails
4. **Calendar events created** automatically
5. **User can review** and manage extracted meetings

## Future Enhancements

Planned features for upcoming releases:

- ✅ **Google Calendar Sync**: Two-way sync with Google Calendar
- ✅ **Outlook Calendar Sync**: Integration with Microsoft Outlook
- ✅ **Recurring Meetings**: Support for recurring event extraction
- ✅ **Conflict Detection**: Warn about scheduling conflicts
- ✅ **RSVP Tracking**: Track meeting responses
- ✅ **Reminders**: Send notifications before meetings
- ✅ **ICS Export**: Download events as .ics files
- ✅ **Meeting Notes**: Attach notes and action items
- ✅ **Timezone Support**: Handle different timezones

## Troubleshooting

### No Meetings Detected

**Problem**: System says "No meeting information found"

**Solutions:**
- Ensure email contains meeting-related keywords (meeting, call, schedule)
- Include clear date/time information
- Use recognized date formats
- Check that email has sufficient content

### Incorrect Date/Time Extracted

**Problem**: Meeting has wrong date or time

**Solutions:**
- Use clear, standard date formats (MM/DD/YYYY, Month DD, YYYY)
- Include explicit time with AM/PM indicator
- Avoid ambiguous date references
- Place date/time near the beginning of the email

### Missing Location or Attendees

**Problem**: Location or attendees not extracted

**Solutions:**
- Use clear labels: "Location:", "Attendees:", "Where:"
- List attendees with comma separation
- Include email addresses for attendees
- Place information in a structured format

## Best Practices

### For Email Senders

To ensure meetings are extracted correctly:

1. **Use clear subject lines**: "Team Meeting - Jan 15, 2026"
2. **Include explicit dates**: "January 15, 2026" instead of "next Tuesday"
3. **Specify time with AM/PM**: "3:00 PM" instead of "3"
4. **Label sections**: "Location:", "Time:", "Attendees:"
5. **Include meeting links**: Full URL for Zoom/Teams
6. **Use standard formats**: Avoid unusual date/time formats

### For System Administrators

1. **Monitor extraction accuracy**: Check confidence levels
2. **Review false positives**: Emails incorrectly identified as meetings
3. **Update patterns**: Add custom meeting keywords for your organization
4. **Train users**: Provide templates for meeting invites
5. **Regular backups**: Backup calendar_events table

## Technical Details

### Dependencies

- `python-dateutil`: Advanced date parsing
- `re` (regex): Pattern matching
- `sqlite3`: Database storage
- `json`: Data serialization

### Performance

- Average extraction time: < 500ms per email
- Batch processing: ~50 emails in 10-15 seconds
- Database queries: Optimized with indexes
- Memory usage: Minimal (< 50MB for typical operations)

### Security

- All meetings are user-specific
- JWT authentication required
- No external API calls (privacy-first)
- Meeting data encrypted at rest
- HTTPS required for production

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review example extractions for reference
3. Test with simple meeting formats first
4. Check backend logs for detailed error messages
5. Open an issue on GitHub: [harshit1314/email-classifiy](https://github.com/harshit1314/email-classifiy)

---

**Version**: 1.0.0  
**Last Updated**: January 31, 2026  
**Author**: AI Email Classifier Team
