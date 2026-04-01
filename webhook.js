const fetch = require('node-fetch');

const BOT_TOKEN = '8486993696:AAFLyvI3lbMYltXTKXVSbMj552dcXaXwgRI';
const SUPABASE_URL = 'https://perxwqxtzgbvswimmkgt.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBlcnh3cXh0emdidnN3aW1ta2d0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwNTY1NTYsImV4cCI6MjA5MDYzMjU1Nn0.dmR6UpUOHsYgPgr8k9wWWiqdNhfGq38Qjk5so1l37YY';

async function updateOrderStatus(orderId, newStatus) {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/orders?order_number=eq.${orderId}`, {
        method: 'PATCH',
        headers: {
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    });
    return response.ok;
}

async function getOrderById(orderId) {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/orders?order_number=eq.${orderId}&select=*`, {
        headers: {
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`
        }
    });
    const data = await response.json();
    return data[0];
}

async function notifyUser(userTgId, orderId, statusText) {
    await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            chat_id: userTgId,
            text: `🔄 Статус вашего заказа #${orderId} изменён на "${statusText}"`,
            parse_mode: 'HTML'
        })
    });
}

async function updateModeratorMessage(chatId, messageId, orderId, statusText) {
    // Получаем текущее сообщение
    const msgResponse = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/getMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId, message_id: messageId })
    });
    const msgData = await msgResponse.json();
    
    if (msgData.ok && msgData.result) {
        const oldText = msgData.result.text;
        const newText = oldText.replace(/🆕 <b>НОВЫЙ ЗАКАЗ/, `🔄 <b>ЗАКАЗ ${statusText.toUpperCase()}</b>`);
        
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/editMessageText`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: chatId,
                message_id: messageId,
                text: newText,
                parse_mode: 'HTML'
            })
        });
    }
}

module.exports = async (req, res) => {
    const update = req.body;
    
    if (!update.callback_query) {
        return res.sendStatus(200);
    }
    
    const callback = update.callback_query;
    const data = callback.data;
    const chatId = callback.message.chat.id;
    const messageId = callback.message.message_id;
    
    const [action, orderId] = data.split('_');
    
    let newStatus = '';
    let statusText = '';
    
    switch (action) {
        case 'view':
            newStatus = 'viewed';
            statusText = 'Просмотрено';
            break;
        case 'paid':
            newStatus = 'paid';
            statusText = 'Оплачен';
            break;
        case 'done':
            newStatus = 'completed';
            statusText = 'Выполнен';
            break;
        default:
            return res.sendStatus(200);
    }
    
    // Обновляем статус в базе
    await updateOrderStatus(orderId, newStatus);
    
    // Получаем заказ, чтобы узнать user_tg_id
    const order = await getOrderById(orderId);
    
    // Обновляем сообщение модератора
    await updateModeratorMessage(chatId, messageId, orderId, statusText);
    
    // Отвечаем на callback (убираем "часики")
    await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/answerCallbackQuery`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            callback_query_id: callback.id,
            text: `Статус изменён на "${statusText}"`,
            show_alert: false
        })
    });
    
    // Уведомляем пользователя
    if (order && order.user_tg_id) {
        await notifyUser(order.user_tg_id, orderId, statusText);
    }
    
    res.sendStatus(200);
};
