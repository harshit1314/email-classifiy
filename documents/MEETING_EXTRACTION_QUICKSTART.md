# Quick Start: Meeting Extraction Feature

## 🚀 Get Started in 3 Steps

### Step 1: Start the Application

```bash
# Backend (Terminal 1)
cd backend
uvicorn app.main:app --reload

# Frontend (Terminal 2)
cd frontend
npm run dev
```

### Step 2: Login

Navigate to http://localhost:5173 and login with:
- Email: `admin@emailclassifier.com`
- Password: `admin123`

### Step 3: Extract Meetings

#### Option A: Manual Extraction
1. Go to **Calendar** page from the sidebar
2. Paste an email containing meeting details
3. Click **"Extract Meeting"**
4. View extracted meeting in the calendar

#### Option B: Auto-Extract
1. Go to **Calendar** page
2. Click **"Auto-Extract from Emails"** button
3. System scans recent emails and extracts all meetings
4. View all extracted meetings in the calendar

---

## 📝 Example Emails to Try

### Example 1: Simple Meeting
```
Subject: Team Standup

Hi team,

Let's meet tomorrow at 10:00 AM in Conference Room B.

See you there!
```

### Example 2: Virtual Meeting
```
Subject: Project Review

Join the project review on January 25, 2026 at 3:00 PM

Zoom: https://zoom.us/j/123456789

Agenda:
- Progress update
- Next steps
- Q&A
```

### Example 3: Detailed Meeting
```
Subject: Client Presentation

Date: February 1, 2026
Time: 2:00 PM - 3:30 PM
Location: Office Building, Room 401
Attendees: client@company.com, team@company.com

Please prepare your slides in advance.
```

---

## 🎯 What Gets Extracted

The AI automatically detects:

- ✅ **Meeting Title** (from subject)
- ✅ **Date** (MM/DD/YYYY, Month DD, relative dates)
- ✅ **Time** (12h/24h format, time ranges)
- ✅ **Location** (physical locations, meeting rooms)
- ✅ **Virtual Links** (Zoom, Teams, Google Meet)
- ✅ **Attendees** (email addresses and names)
- ✅ **Duration** (start and end times)

---

## 💡 Tips for Best Results

1. **Use clear dates**: "January 15, 2026" instead of "next week"
2. **Include time with AM/PM**: "3:00 PM" instead of "15:00"
3. **Label sections**: Use "Location:", "Time:", "Attendees:"
4. **Include meeting keywords**: meeting, call, conference, zoom
5. **Add virtual links**: Full URLs for online meetings

---

## 📱 Features

- **Upcoming Events Sidebar**: See next 5 meetings at a glance
- **Interactive Calendar**: Click dates to view scheduled events
- **Confidence Badges**: Know which meetings were extracted with high confidence
- **Auto-Scheduling**: Meetings are saved automatically to your calendar
- **Batch Processing**: Extract from multiple emails at once

---

## 🔧 Troubleshooting

**Problem**: No meetings detected
- **Solution**: Add meeting keywords (meeting, call, schedule)
- **Solution**: Include clear date and time

**Problem**: Wrong date extracted
- **Solution**: Use standard date formats (MM/DD/YYYY)
- **Solution**: Avoid ambiguous date references

**Problem**: Missing location
- **Solution**: Use label "Location:" before the location
- **Solution**: Include full virtual meeting URLs

---

## 📚 More Information

- Full Documentation: [MEETING_EXTRACTION_GUIDE.md](MEETING_EXTRACTION_GUIDE.md)
- API Documentation: http://localhost:8000/docs (when backend is running)
- Support: [GitHub Issues](https://github.com/harshit1314/email-classifiy/issues)

---

**Happy Scheduling! 🎉**
