const express = require('express');
const cors = require('cors');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
const rooms = {};
function generateRoomCode() {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}
app.post('/api/create-room', (req, res) => {
  const { creatorCode, maxUsers } = req.body;
  if (creatorCode !== 'makehogamdoroom') {
    return res.status(403).json({ error: '제작자 코드가 일치하지 않습니다.' });
  }
  if (!maxUsers || isNaN(maxUsers) || maxUsers < 1) {
    return res.status(400).json({ error: '유효한 인원수를 설정해주세요.' });
  }
  const roomCode = generateRoomCode();
  rooms[roomCode] = {
    maxUsers: parseInt(maxUsers, 10),
    participants: []
  };
  res.json({ roomCode, maxUsers: rooms[roomCode].maxUsers });
});
app.post('/api/join-room', (req, res) => {
  const { roomCode, name, studentId, picks } = req.body;
  const room = rooms[roomCode];
  if (!room) {
    return res.status(404).json({ error: '존재하지 않는 방입니다.' });
  }
  if (room.participants.length >= room.maxUsers) {
    const existing = room.participants.find(p => p.studentId === studentId);
    if (!existing) {
       return res.status(403).json({ error: '방 인원이 모두 차서 입장할 수 없습니다.' });
    }
  } else {
    const existingIndex = room.participants.findIndex(p => p.studentId === studentId);
    if (existingIndex !== -1) {
        room.participants[existingIndex] = { name, studentId, picks };
    } else {
        room.participants.push({ name, studentId, picks });
    }
  }
  res.json({ success: true, currentUsers: room.participants.length, maxUsers: room.maxUsers });
});
app.get('/api/room-status/:roomCode', (req, res) => {
  const { roomCode } = req.params;
  const { studentId } = req.query; 
  const room = rooms[roomCode];
  if (!room) {
    return res.status(404).json({ error: '존재하지 않는 방입니다.' });
  }
  const isReady = room.participants.length >= room.maxUsers;
  if (!isReady) {
    return res.json({ 
      isReady: false, 
      currentUsers: room.participants.length, 
      maxUsers: room.maxUsers 
    });
  }
  let myResults = null;
  if (studentId) {
    const me = room.participants.find(p => p.studentId === studentId);
    if (me) {
      myResults = [];
      for (let i = 0; i < 5; i++) {
        const targetId = me.picks[i];
        if (!targetId) {
          myResults.push(null);
          continue;
        }
        const target = room.participants.find(p => p.studentId === targetId);
        if (!target) {
          myResults.push(null); 
        } else {
          const myRankIndex = target.picks.indexOf(me.studentId);
          if (myRankIndex !== -1) {
            myResults.push(myRankIndex + 1);
          } else {
            myResults.push(null);
          }
        }
      }
    }
  }
  res.json({
    isReady: true,
    results: myResults
  });
});
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});