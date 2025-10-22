# Chat History Feature

This document describes the new chat history functionality added to the AI Agent system.

## Features

### 1. Collapsible Sidebar
- **Toggle Button**: Click the hamburger menu (☰) in the header to open/close the sidebar
- **Mobile Responsive**: On mobile devices, the sidebar overlays the main content with a backdrop
- **Auto-close**: Sidebar automatically closes when loading a chat on mobile

### 2. Chat History Management
- **View All Chats**: See all previous conversations with timestamps and previews
- **Search Chats**: Use the search box to filter chats by content or filename
- **Load Previous Chats**: Click on any chat to load and continue the conversation
- **Delete Chats**: Remove unwanted chat histories with the delete button

### 3. API Endpoints
The following new API endpoints have been added:

- `GET /api/chat-history` - List all available chat histories
- `GET /api/chat-history/{chat_id}` - Get full content of a specific chat
- `POST /api/chat-history/{chat_id}/load` - Load a chat into a session
- `DELETE /api/chat-history/{chat_id}` - Delete a specific chat

### 4. WebSocket Integration
- **Session Management**: Each WebSocket connection gets a unique session ID
- **Chat Loading**: Use `/load_chat {chat_id}` command to load previous conversations
- **Real-time Updates**: Chat history refreshes automatically every 30 seconds

## Usage

### Loading a Previous Chat
1. Click the hamburger menu (☰) to open the sidebar
2. Browse or search for the chat you want to continue
3. Click on the chat item or use the "Load" button
4. The conversation will be loaded and you can continue chatting

### Managing Chat History
- **Search**: Type in the search box to filter chats by content
- **Delete**: Click the "Delete" button on any chat to remove it
- **Refresh**: Chat history automatically refreshes every 30 seconds

### Mobile Usage
- On mobile devices, the sidebar becomes a full-screen overlay
- Tap outside the sidebar or use the close button to dismiss it
- The sidebar automatically closes when you load a chat

## Technical Details

### File Structure
- Chat transcripts are stored in `logs/transcripts/`
- Action logs are stored in `logs/actions/`
- Files are named with timestamp format: `conversation_YYYYMMDD_HHMMSS.log`

### Data Format
Each chat history item includes:
- `id`: Unique identifier (filename)
- `timestamp`: ISO format timestamp
- `preview`: First 200 characters of the conversation
- `size`: File size in bytes
- `created`: Creation timestamp
- `modified`: Last modification timestamp

### Browser Compatibility
- Modern browsers with WebSocket support
- Responsive design works on desktop, tablet, and mobile
- No additional dependencies required

## Security Notes
- Chat history is stored locally on the server
- No authentication required for WebSocket connections (main page is still protected)
- Consider implementing proper WebSocket authentication for production use

## Future Enhancements
- Chat export/import functionality
- Chat categorization and tagging
- Advanced search with filters
- Chat sharing between users
- Automatic chat archiving

