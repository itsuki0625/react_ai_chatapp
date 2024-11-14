const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

const instruction = fs.readFileSync('./instruction.md', 'utf8');

app.post('/chat', async (req, res) => {
    const userMessage = req.body.message;
    const messageHistory = req.body.history || [];

    try {
        // 会話履歴をOpenAIのフォーマットに変換
        const formattedHistory = messageHistory.map(msg => ({
            role: msg.sender.toLowerCase() === 'ai' ? 'assistant' : 'user',
            content: msg.text
        }));

        // システムメッセージと会話履歴を含めたメッセージ配列を作成
        const messages = [
            { role: 'system', content: instruction },
            ...formattedHistory,
            { role: 'user', content: userMessage }
        ];

        const response = await axios.post('https://api.openai.com/v1/chat/completions', {
            model: 'gpt-4o-mini',
            messages: messages,
            temperature: 0.7,
            max_tokens: 1000
        }, {
            headers: {
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                'Content-Type': 'application/json',
                'OpenAI-Project': 'proj_d7ZsBHltTrUoVHZdsm8adVlM',
            },
        });

        console.log('AI応答:', response.data.choices[0].message.content);

        res.json({
            replay: response.data.choices[0].message.content,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('エラー詳細:', error.response?.data || error.message);
        res.status(500).json({
            error: 'エラーが発生しました。',
            details: error.response?.data || error.message
        });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`サーバーがポート${PORT}で起動しました。`);
});
