// frontend/src/App.tsx
import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // 新增：用于存储当前正在调用的工具状态
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到最新消息或工具状态
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, toolStatus]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');

    // 1. 构建包含历史记录的完整消息列表
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);
    setToolStatus(null); // 重置工具状态

    try {
      // 2. 接口路径更新为 /api/chat，并传入完整 messages 数组
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages }),
      });

      if (!response.body) throw new Error('ReadableStream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let assistantContent = '';
      let buffer = ''; // 新增：流式字符串缓冲区，防止 JSON 截断

      // 先插入一个空的 assistant 消息占位
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk; // 将新收到的数据放入缓冲区

        // 按照换行符拆分（SSE 标准格式每个 data 后面跟 \n\n）
        const lines = buffer.split('\n');

        // 将最后一行（可能不完整的片段）留给下一个 chunk 处理
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim().startsWith('data:')) {
            const dataStr = line.replace('data:', '').trim();

            if (dataStr === '[DONE]') {
              setToolStatus(null); // 对话结束，清除工具状态
              break;
            }

            try {
              // 3. 解析结构化的 JSON 数据
              const data = JSON.parse(dataStr);

              if (data.type === 'content') {
                // 正常的文本流式输出
                assistantContent += data.content;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = assistantContent;
                  return updated;
                });
              }
              else if (data.type === 'tool_start') {
                // 工具开始调用：更新 UI 提示
                const name = data.tool_name === 'simple_calculator' ? '计算器' :
                             data.tool_name === 'get_current_time' ? '时间工具' :
                             data.tool_name === 'query_campus_knowledge_base' ? '校园知识库' : data.tool_name;
                setToolStatus(`正在调用: ${name}...`);
              }
              else if (data.type === 'tool_end') {
                // 工具调用结束
                setToolStatus(null);
              }
              else if (data.type === 'error') {
                // 后端报错处理
                assistantContent += `\n\n[系统错误: ${data.content}]`;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = assistantContent;
                  return updated;
                });
              }
            } catch {
              // 如果 JSON 依然无法解析，忽略这条残缺的数据
              console.warn("JSON parse error for stream chunk:", dataStr);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: '请求出错，请检查后端服务是否启动。' }]);
    } finally {
      setIsLoading(false);
      setToolStatus(null);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 max-w-4xl mx-auto border shadow-sm">
      <header className="p-4 bg-white border-b text-lg font-bold text-gray-800">
        Campus AI Agent Platform - v0.3
      </header>

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-3 rounded-lg max-w-[70%] ${
              msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border text-gray-800 whitespace-pre-wrap'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}

        {/* 新增：动态展示工具调用状态 */}
        {toolStatus && (
          <div className="flex justify-start animate-pulse">
            <div className="px-4 py-2 bg-blue-50 text-blue-600 rounded-full text-sm font-medium border border-blue-100 shadow-sm">
              {toolStatus}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      <footer className="p-4 bg-white border-t">
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入校园服务问题，例如：学生手册里请假流程是什么？"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            disabled={isLoading}
          />
          <button
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            onClick={sendMessage}
            disabled={isLoading}
          >
            发送
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;
