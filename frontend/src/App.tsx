// frontend/src/App.tsx
import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type UserRole = 'guest' | 'student' | 'admin';

interface TraceSource {
  title: string;
  category: string;
  page: string;
  summary: string;
}

interface TraceItem {
  message: string;
  sources?: TraceSource[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  traces?: TraceItem[];
}

interface AuthUser {
  id: number | null;
  username: string;
  display_name: string;
  role: UserRole;
  is_guest: boolean;
}

interface AuthResponse {
  access_token: string;
  user: AuthUser;
}

type AccessLevel = 'public' | 'student' | 'admin';
type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'deleted';

interface KnowledgeDocument {
  id: string;
  title: string;
  original_filename: string;
  file_ext: string;
  file_size: number;
  content_type: string | null;
  category: string;
  access_level: AccessLevel;
  storage_path: string;
  status: DocumentStatus;
  chunk_count: number;
  uploaded_by_id: number | null;
  uploaded_by_username: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

type IconName =
  | 'book'
  | 'brain'
  | 'clock'
  | 'database'
  | 'login'
  | 'network'
  | 'search'
  | 'send'
  | 'shield'
  | 'spark'
  | 'tool';

interface QuickPrompt {
  title: string;
  text: string;
  icon: IconName;
}

const TOKEN_STORAGE_KEY = 'campus_ai_access_token';

const guestUser: AuthUser = {
  id: null,
  username: 'guest',
  display_name: '访客',
  role: 'guest',
  is_guest: true,
};

const roleLabels: Record<UserRole, string> = {
  guest: '访客',
  student: '用户',
  admin: '管理员',
};

const accessLevelLabels: Record<AccessLevel, string> = {
  public: '公开',
  student: '学生',
  admin: '管理员',
};

const documentStatusLabels: Record<DocumentStatus, string> = {
  pending: '等待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
  deleted: '已删除',
};

const quickPrompts: QuickPrompt[] = [
  {
    title: '校规问答',
    text: '学生手册里请假流程是什么？',
    icon: 'book',
  },
  {
    title: '网络服务',
    text: '校园网常见故障怎么处理？',
    icon: 'network',
  },
  {
    title: '开放时间',
    text: '图书馆开放时间有哪些规定？',
    icon: 'clock',
  },
  {
    title: '奖助申请',
    text: '帮我查询奖学金申请条件',
    icon: 'shield',
  },
];

const campusScenes = ['规章制度问答', '办事流程查询', '校园服务咨询', '知识库溯源'];

const formatFileSize = (size: number) => {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
};

const formatDateTime = (value: string | null) => {
  if (!value) return '-';
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
};

function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  const common = {
    className,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };

  switch (name) {
    case 'book':
      return (
        <svg {...common}>
          <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
          <path d="M4 5.5v16" />
          <path d="M8 7h8" />
          <path d="M8 11h6" />
        </svg>
      );
    case 'brain':
      return (
        <svg {...common}>
          <path d="M9 4.5a3 3 0 0 0-3 3v.3A3.2 3.2 0 0 0 4 11a3.3 3.3 0 0 0 2 3v.5a3 3 0 0 0 5.3 1.9" />
          <path d="M15 4.5a3 3 0 0 1 3 3v.3A3.2 3.2 0 0 1 20 11a3.3 3.3 0 0 1-2 3v.5a3 3 0 0 1-5.3 1.9" />
          <path d="M12 5v14" />
          <path d="M8 10h2" />
          <path d="M14 10h2" />
        </svg>
      );
    case 'clock':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 7.5V12l3.2 2" />
        </svg>
      );
    case 'database':
      return (
        <svg {...common}>
          <ellipse cx="12" cy="5.5" rx="7" ry="3" />
          <path d="M5 5.5v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
          <path d="M5 11.5v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
        </svg>
      );
    case 'login':
      return (
        <svg {...common}>
          <path d="M15 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-3" />
          <path d="M10 17l5-5-5-5" />
          <path d="M15 12H4" />
        </svg>
      );
    case 'network':
      return (
        <svg {...common}>
          <circle cx="6" cy="7" r="2.5" />
          <circle cx="18" cy="7" r="2.5" />
          <circle cx="12" cy="18" r="2.5" />
          <path d="m8 8.6 2.7 6" />
          <path d="m16 8.6-2.7 6" />
          <path d="M8.5 7h7" />
        </svg>
      );
    case 'search':
      return (
        <svg {...common}>
          <circle cx="11" cy="11" r="6.5" />
          <path d="m16 16 4 4" />
        </svg>
      );
    case 'send':
      return (
        <svg {...common}>
          <path d="m21 3-6.8 18-3.6-7.6L3 9.8z" />
          <path d="m21 3-10.4 10.4" />
        </svg>
      );
    case 'shield':
      return (
        <svg {...common}>
          <path d="M12 3 19 6v5.5c0 4.2-2.8 7.7-7 9.5-4.2-1.8-7-5.3-7-9.5V6z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      );
    case 'spark':
      return (
        <svg {...common}>
          <path d="m12 3 1.6 5.2L19 10l-5.4 1.8L12 17l-1.6-5.2L5 10l5.4-1.8z" />
          <path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z" />
        </svg>
      );
    case 'tool':
      return (
        <svg {...common}>
          <path d="M14.7 6.3a4 4 0 0 0 5 5L11 20l-4-4z" />
          <path d="m6.5 16.5 1 1" />
        </svg>
      );
  }
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY) || '');
  const [currentUser, setCurrentUser] = useState<AuthUser>(guestUser);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [isAuthSubmitting, setIsAuthSubmitting] = useState(false);
  const [isCreateUserOpen, setIsCreateUserOpen] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newDisplayName, setNewDisplayName] = useState('');
  const [newRole, setNewRole] = useState<'student' | 'admin'>('student');
  const [createUserError, setCreateUserError] = useState('');
  const [createUserSuccess, setCreateUserSuccess] = useState('');
  const [isCreateUserSubmitting, setIsCreateUserSubmitting] = useState(false);
  const [isKnowledgeOpen, setIsKnowledgeOpen] = useState(false);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCategory, setUploadCategory] = useState('general');
  const [uploadAccessLevel, setUploadAccessLevel] = useState<AccessLevel>('public');
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [isUploadingDocument, setIsUploadingDocument] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, toolStatus]);

  useEffect(() => {
    if (!authToken) {
      setCurrentUser(guestUser);
      return;
    }

    let ignore = false;
    const loadCurrentUser = async () => {
      try {
        const response = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        if (!response.ok) throw new Error('token invalid');
        const user = await response.json() as AuthUser;
        if (!ignore) setCurrentUser(user);
      } catch {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        if (!ignore) {
          setAuthToken('');
          setCurrentUser(guestUser);
        }
      }
    };

    void loadCurrentUser();
    return () => {
      ignore = true;
    };
  }, [authToken]);

  const resetAuthForm = () => {
    setAuthUsername('');
    setAuthPassword('');
    setAuthError('');
  };

  const openAuthDialog = () => {
    resetAuthForm();
    setIsAuthOpen(true);
  };

  const resetCreateUserForm = () => {
    setNewUsername('');
    setNewPassword('');
    setNewDisplayName('');
    setNewRole('student');
    setCreateUserError('');
    setCreateUserSuccess('');
  };

  const openCreateUserDialog = () => {
    resetCreateUserForm();
    setIsCreateUserOpen(true);
  };

  const loadKnowledgeDocuments = useCallback(async () => {
    if (currentUser.role !== 'admin' || !authToken) return;

    setIsDocumentsLoading(true);
    setDocumentsError('');

    try {
      const response = await fetch('/api/knowledge/documents', {
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(errorData?.detail || '加载文档列表失败');
      }

      const data = await response.json() as KnowledgeDocument[];
      setDocuments(data);
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : '加载文档列表失败');
    } finally {
      setIsDocumentsLoading(false);
    }
  }, [authToken, currentUser.role]);

  useEffect(() => {
    if (!isKnowledgeOpen || currentUser.role !== 'admin') return;

    const intervalId = window.setInterval(() => {
      void loadKnowledgeDocuments();
    }, 4000);

    return () => window.clearInterval(intervalId);
  }, [currentUser.role, isKnowledgeOpen, loadKnowledgeDocuments]);

  const resetUploadForm = () => {
    setUploadFile(null);
    setUploadTitle('');
    setUploadCategory('general');
    setUploadAccessLevel('public');
    setUploadError('');
    setFileInputKey((key) => key + 1);
  };

  const openKnowledgeDialog = () => {
    setIsKnowledgeOpen(true);
    setUploadError('');
    setUploadSuccess('');
    void loadKnowledgeDocuments();
  };

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setAuthToken('');
    setCurrentUser(guestUser);
    setIsCreateUserOpen(false);
    setIsKnowledgeOpen(false);
  };

  const handleAuthSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!authUsername.trim() || !authPassword) return;

    setIsAuthSubmitting(true);
    setAuthError('');

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: authUsername.trim(),
          password: authPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(errorData?.detail || '认证失败');
      }

      const data = await response.json() as AuthResponse;
      localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
      setAuthToken(data.access_token);
      setCurrentUser(data.user);
      setIsAuthOpen(false);
      resetAuthForm();
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : '认证失败');
    } finally {
      setIsAuthSubmitting(false);
    }
  };

  const handleCreateUserSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newUsername.trim() || !newPassword || currentUser.role !== 'admin') return;

    setIsCreateUserSubmitting(true);
    setCreateUserError('');
    setCreateUserSuccess('');

    try {
      const response = await fetch('/api/auth/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          username: newUsername.trim(),
          password: newPassword,
          display_name: newDisplayName.trim() || undefined,
          role: newRole,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(errorData?.detail || '创建用户失败');
      }

      const createdUser = await response.json() as AuthUser;
      setCreateUserSuccess(`已创建用户：${createdUser.username}（${roleLabels[createdUser.role]}）`);
      setNewUsername('');
      setNewPassword('');
      setNewDisplayName('');
      setNewRole('student');
    } catch (error) {
      setCreateUserError(error instanceof Error ? error.message : '创建用户失败');
    } finally {
      setIsCreateUserSubmitting(false);
    }
  };

  const handleUploadDocumentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!uploadFile || currentUser.role !== 'admin') return;

    setIsUploadingDocument(true);
    setUploadError('');
    setUploadSuccess('');

    const formData = new FormData();
    formData.append('file', uploadFile);
    if (uploadTitle.trim()) formData.append('title', uploadTitle.trim());
    formData.append('category', uploadCategory.trim() || 'general');
    formData.append('access_level', uploadAccessLevel);

    try {
      const response = await fetch('/api/knowledge/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(errorData?.detail || '上传文档失败');
      }

      const document = await response.json() as KnowledgeDocument;
      setUploadSuccess(`已创建处理任务：${document.title}`);
      resetUploadForm();
      await loadKnowledgeDocuments();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : '上传文档失败');
    } finally {
      setIsUploadingDocument(false);
    }
  };

  const handleDeleteDocument = async (document: KnowledgeDocument) => {
    if (currentUser.role !== 'admin') return;
    const confirmed = window.confirm(`确定删除《${document.title}》吗？这会删除源文件和对应的 Milvus 切片。`);
    if (!confirmed) return;

    setDeletingDocumentId(document.id);
    setDocumentsError('');

    try {
      const response = await fetch(`/api/knowledge/documents/${document.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(errorData?.detail || '删除文档失败');
      }

      await loadKnowledgeDocuments();
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : '删除文档失败');
    } finally {
      setDeletingDocumentId(null);
    }
  };

  const appendTraceToLastAssistant = (trace: TraceItem) => {
    setMessages(prev => {
      const updated = [...prev];
      const lastMessage = updated[updated.length - 1];
      if (!lastMessage || lastMessage.role !== 'assistant') return prev;

      const traces = lastMessage.traces || [];
      const hasSameTrace = traces.some(item =>
        item.message === trace.message &&
        JSON.stringify(item.sources || []) === JSON.stringify(trace.sources || [])
      );
      if (hasSameTrace) return prev;

      updated[updated.length - 1] = {
        ...lastMessage,
        traces: [...traces, trace],
      };
      return updated;
    });
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');

    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);
    setToolStatus(null);

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (authToken) headers.Authorization = `Bearer ${authToken}`;

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          messages: newMessages.map(({ role, content }) => ({ role, content })),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(errorData?.detail || '请求失败');
      }
      if (!response.body) throw new Error('ReadableStream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let assistantContent = '';
      let buffer = '';

      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: '', traces: [{ message: '正在理解问题' }] },
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim().startsWith('data:')) {
            const dataStr = line.replace('data:', '').trim();

            if (dataStr === '[DONE]') {
              setToolStatus(null);
              break;
            }

            try {
              const data = JSON.parse(dataStr);

              if (data.type === 'content') {
                assistantContent += data.content;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = assistantContent;
                  return updated;
                });
              }
              else if (data.type === 'trace') {
                appendTraceToLastAssistant({
                  message: data.message,
                  sources: data.sources,
                });
              }
              else if (data.type === 'tool_start') {
                const name = data.tool_name === 'simple_calculator' ? '计算器' :
                             data.tool_name === 'get_current_time' ? '时间工具' :
                             data.tool_name === 'query_campus_knowledge_base' ? '校园知识库' : data.tool_name;
                setToolStatus(`正在调用: ${name}...`);
              }
              else if (data.type === 'tool_end') {
                setToolStatus(null);
              }
              else if (data.type === 'error') {
                assistantContent += `\n\n[系统错误: ${data.content}]`;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = assistantContent;
                  return updated;
                });
              }
            } catch {
              console.warn('JSON parse error for stream chunk:', dataStr);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      const message = error instanceof Error ? error.message : '请求出错，请检查后端服务是否启动。';
      setMessages(prev => {
        const updated = [...prev];
        const lastMessage = updated[updated.length - 1];
        if (lastMessage?.role === 'assistant' && !lastMessage.content) {
          updated[updated.length - 1] = { ...lastMessage, content: message };
          return updated;
        }
        return [...prev, { role: 'assistant', content: message }];
      });
    } finally {
      setIsLoading(false);
      setToolStatus(null);
    }
  };

  return (
    <div className="campus-app">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">
            <span />
          </div>
          <div>
            <h1>Campus AI Agent Platform</h1>
            <p>校园知识中枢</p>
          </div>
        </div>

        <div className="topbar-actions">
          <div className="health-card user-card" aria-label="当前用户">
            <span className={`status-light role-${currentUser.role}`} />
            <div>
              <strong>{roleLabels[currentUser.role]}</strong>
              <small>{currentUser.is_guest ? '未登录访客' : currentUser.display_name}</small>
            </div>
          </div>
          <button
            type="button"
            className="login-button"
            title={currentUser.is_guest ? '登录账号' : '退出登录'}
            onClick={() => currentUser.is_guest ? openAuthDialog() : handleLogout()}
          >
            <Icon name="login" className="button-icon" />
            {currentUser.is_guest ? '登录' : '退出'}
          </button>
          {currentUser.role === 'admin' && (
            <>
              <button
                type="button"
                className="admin-button"
                title="管理知识库文档"
                onClick={openKnowledgeDialog}
              >
                <Icon name="database" className="button-icon" />
                知识库
              </button>
              <button
                type="button"
                className="admin-button"
                title="添加平台用户"
                onClick={openCreateUserDialog}
              >
                <Icon name="shield" className="button-icon" />
                添加用户
              </button>
            </>
          )}
        </div>
      </header>

      <div className="app-grid">
        <aside className="insight-rail">
          <section className="visual-card assistant-card">
            <div className="assistant-core" aria-hidden="true">
              <div className="core-panel">
                <div className="core-chip">AI</div>
                <div className="core-line core-line-a" />
                <div className="core-line core-line-b" />
                <div className="core-node node-a" />
                <div className="core-node node-b" />
                <div className="core-node node-c" />
              </div>
            </div>
            <div className="assistant-copy">
              <span className="section-kicker">Campus Copilot</span>
              <h2>一个入口处理校园问题</h2>
              <p>把知识检索、规则问答和工具调用收进同一个对话工作流。</p>
            </div>
          </section>

          <section className="panel-card scene-card">
            <div className="panel-title">
              <Icon name="search" className="panel-title-icon" />
              高频场景
            </div>
            <div className="scene-list">
              {campusScenes.map((item, index) => (
                <div className="scene-item" key={item}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  {item}
                </div>
              ))}
            </div>
          </section>
        </aside>

        <main className="chat-shell">
          <section className="chat-header">
            <div className="assistant-identity">
              <div className="assistant-avatar" aria-hidden="true">
                <Icon name="brain" />
              </div>
              <div>
                <h2>Campus AI Assistant</h2>
                <p>当前身份：{roleLabels[currentUser.role]} · 面向高校场景的 AI Agent 对话入口</p>
              </div>
            </div>

            <div className="chat-header-meta">
              {toolStatus ? (
                <div className="tool-status">
                  <Icon name="tool" />
                  {toolStatus}
                </div>
              ) : (
                <div className="tool-status idle">
                  <Icon name="database" />
                  {currentUser.role === 'guest' ? '仅访问公开知识' : '知识库权限已同步'}
                </div>
              )}
            </div>
          </section>

          <section className="message-area">
            {messages.length === 0 ? (
              <div className="welcome-layout">
                <div className="campus-illustration" aria-hidden="true">
                  <div className="campus-sky">
                    <div className="data-track track-one" />
                    <div className="data-track track-two" />
                  </div>
                  <div className="campus-building building-left" />
                  <div className="campus-building building-main">
                    <div className="building-roof" />
                    <div className="building-window window-a" />
                    <div className="building-window window-b" />
                    <div className="building-window window-c" />
                  </div>
                  <div className="campus-building building-right" />
                  <div className="campus-gate">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>

                <div className="welcome-copy">
                  <span className="section-kicker">智能校园服务台</span>
                  <h3>把问题交给校园 AI 助手</h3>
                  <p>选择一个常见问题，或直接输入你的需求。系统会根据当前身份决定可访问的校园知识范围。</p>
                </div>

                <div className="quick-grid">
                  {quickPrompts.map(prompt => (
                    <button
                      key={prompt.title}
                      type="button"
                      className="quick-card"
                      onClick={() => setInput(prompt.text)}
                      disabled={isLoading}
                    >
                      <span className="quick-icon">
                        <Icon name={prompt.icon} />
                      </span>
                      <span className="quick-title">{prompt.title}</span>
                      <span className="quick-text">{prompt.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="message-stack">
                {messages.map((msg, idx) => {
                  const isUser = msg.role === 'user';
                  const isLastAssistant = !isUser && idx === messages.length - 1 && isLoading && !msg.content;

                  return (
                    <div key={idx} className={`message-row ${isUser ? 'from-user' : 'from-assistant'}`}>
                      {!isUser && (
                        <div className="message-avatar assistant">
                          <Icon name="brain" />
                        </div>
                      )}
                      <div className="message-content">
                        <div className="message-author">{isUser ? currentUser.display_name : 'Campus AI Assistant'}</div>
                        {!isUser && msg.traces?.length ? (
                          <div className="trace-card">
                            <div className="trace-title">处理过程 / 执行轨迹</div>
                            <div className="trace-list">
                              {msg.traces.map((trace, traceIndex) => (
                                <div className="trace-item" key={`${trace.message}-${traceIndex}`}>
                                  <div className="trace-line">
                                    <span>{traceIndex + 1}</span>
                                    {trace.message}
                                  </div>
                                  {trace.sources?.length ? (
                                    <div className="trace-sources">
                                      {trace.sources.map((source, sourceIndex) => (
                                        <div className="trace-source" key={`${source.title}-${source.page}-${sourceIndex}`}>
                                          <strong>{source.title}</strong>
                                          <small>分类：{source.category} · 页码：{source.page}</small>
                                          <p>{source.summary}</p>
                                        </div>
                                      ))}
                                    </div>
                                  ) : null}
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        <div className={`message-bubble ${isUser ? 'plain-content' : 'markdown-content'}`}>
                          {isLastAssistant ? (
                            <span className="typing-dots" aria-label="正在思考">
                              <i />
                              <i />
                              <i />
                            </span>
                          ) : isUser ? (
                            msg.content
                          ) : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {msg.content}
                            </ReactMarkdown>
                          )}
                        </div>
                      </div>
                      {isUser && <div className="message-avatar user">{currentUser.is_guest ? '客' : '我'}</div>}
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>
            )}
          </section>

          <footer className="composer-shell">
            <form
              className="composer"
              onSubmit={(event) => {
                event.preventDefault();
                void sendMessage();
              }}
            >
              <div className="composer-leading" aria-hidden="true">
                <Icon name="search" />
              </div>
              <textarea
                placeholder="输入校园服务问题，例如：学生手册里请假流程是什么？"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    void sendMessage();
                  }
                }}
                disabled={isLoading}
                rows={1}
              />
              <button type="submit" className="send-button" disabled={isLoading || !input.trim()}>
                <Icon name="send" />
                发送
              </button>
            </form>
          </footer>
        </main>
      </div>

      {isAuthOpen && (
        <div className="auth-overlay" role="presentation" onMouseDown={() => setIsAuthOpen(false)}>
          <section className="auth-dialog" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="auth-close" onClick={() => setIsAuthOpen(false)} aria-label="关闭登录窗口">
              ×
            </button>
            <div className="auth-hero">
              <div className="assistant-avatar">
                <Icon name="shield" />
              </div>
              <div>
                <span className="section-kicker">身份认证</span>
                <h2>登录校园账号</h2>
                <p>登录后将按角色访问对应级别的校园知识库。</p>
              </div>
            </div>

            <div className="auth-notice">如需注册请联系管理员：abc@example.com</div>

            <form className="auth-form" onSubmit={(event) => void handleAuthSubmit(event)}>
              <label>
                用户名
                <input
                  value={authUsername}
                  onChange={(event) => setAuthUsername(event.target.value)}
                  placeholder="例如 admin 或 student001"
                  autoComplete="username"
                  required
                />
              </label>
              <label>
                密码
                <input
                  type="password"
                  value={authPassword}
                  onChange={(event) => setAuthPassword(event.target.value)}
                  placeholder="至少 6 位"
                  autoComplete="current-password"
                  required
                />
              </label>

              {authError && <div className="auth-error">{authError}</div>}

              <button className="auth-submit" type="submit" disabled={isAuthSubmitting}>
                {isAuthSubmitting ? '处理中...' : '登录'}
              </button>
              <p className="auth-hint">开发默认管理员：admin / admin123456</p>
            </form>
          </section>
        </div>
      )}

      {isKnowledgeOpen && currentUser.role === 'admin' && (
        <div className="auth-overlay" role="presentation" onMouseDown={() => setIsKnowledgeOpen(false)}>
          <section className="auth-dialog knowledge-dialog" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="auth-close" onClick={() => setIsKnowledgeOpen(false)} aria-label="关闭知识库管理窗口">
              ×
            </button>
            <div className="auth-hero">
              <div className="assistant-avatar">
                <Icon name="database" />
              </div>
              <div>
                <span className="section-kicker">知识库管理</span>
                <h2>上传与管理文档</h2>
                <p>源文件会保存到后端 storage 目录，后台处理完成后写入 Milvus。</p>
              </div>
            </div>

            <div className="knowledge-layout">
              <form className="knowledge-upload" onSubmit={(event) => void handleUploadDocumentSubmit(event)}>
                <div className="knowledge-section-title">上传文档</div>
                <label>
                  文件
                  <input
                    key={fileInputKey}
                    type="file"
                    accept=".pdf,.docx,.md,.txt"
                    onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
                    required
                  />
                </label>
                <div className="knowledge-form-grid">
                  <label>
                    标题
                    <input
                      value={uploadTitle}
                      onChange={(event) => setUploadTitle(event.target.value)}
                      placeholder="默认使用文件名"
                    />
                  </label>
                  <label>
                    分类
                    <input
                      value={uploadCategory}
                      onChange={(event) => setUploadCategory(event.target.value)}
                      placeholder="general"
                      required
                    />
                  </label>
                  <label>
                    权限
                    <select value={uploadAccessLevel} onChange={(event) => setUploadAccessLevel(event.target.value as AccessLevel)}>
                      <option value="public">公开</option>
                      <option value="student">学生</option>
                      <option value="admin">管理员</option>
                    </select>
                  </label>
                </div>

                {uploadError && <div className="auth-error">{uploadError}</div>}
                {uploadSuccess && <div className="auth-success">{uploadSuccess}</div>}

                <button className="auth-submit" type="submit" disabled={isUploadingDocument || !uploadFile}>
                  {isUploadingDocument ? '上传中...' : '上传并处理'}
                </button>
              </form>

              <div className="knowledge-documents">
                <div className="knowledge-list-head">
                  <div>
                    <div className="knowledge-section-title">文档列表</div>
                    <p>{documents.length} 个文档，后台状态会自动刷新</p>
                  </div>
                  <button type="button" className="ghost-button" onClick={() => void loadKnowledgeDocuments()} disabled={isDocumentsLoading}>
                    {isDocumentsLoading ? '刷新中' : '刷新'}
                  </button>
                </div>

                {documentsError && <div className="auth-error">{documentsError}</div>}

                <div className="document-list">
                  {isDocumentsLoading && documents.length === 0 ? (
                    <div className="empty-documents">正在加载文档...</div>
                  ) : documents.length === 0 ? (
                    <div className="empty-documents">还没有上传文档</div>
                  ) : (
                    documents.map((document) => (
                      <article className="document-item" key={document.id}>
                        <div className="document-main">
                          <div>
                            <h3>{document.title}</h3>
                            <p>{document.original_filename}</p>
                          </div>
                          <span className={`status-pill status-${document.status}`}>
                            {documentStatusLabels[document.status]}
                          </span>
                        </div>

                        <div className="document-meta">
                          <span>{document.category}</span>
                          <span>{accessLevelLabels[document.access_level]}</span>
                          <span>{formatFileSize(document.file_size)}</span>
                          <span>{document.chunk_count} chunks</span>
                          <span>{formatDateTime(document.created_at)}</span>
                        </div>

                        {document.error_message && (
                          <div className="document-error">{document.error_message}</div>
                        )}

                        <div className="document-actions">
                          <span>上传人：{document.uploaded_by_username}</span>
                          <button
                            type="button"
                            className="danger-button"
                            onClick={() => void handleDeleteDocument(document)}
                            disabled={deletingDocumentId === document.id}
                          >
                            {deletingDocumentId === document.id ? '删除中' : '删除'}
                          </button>
                        </div>
                      </article>
                    ))
                  )}
                </div>
              </div>
            </div>
          </section>
        </div>
      )}

      {isCreateUserOpen && currentUser.role === 'admin' && (
        <div className="auth-overlay" role="presentation" onMouseDown={() => setIsCreateUserOpen(false)}>
          <section className="auth-dialog" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="auth-close" onClick={() => setIsCreateUserOpen(false)} aria-label="关闭添加用户窗口">
              ×
            </button>
            <div className="auth-hero">
              <div className="assistant-avatar">
                <Icon name="shield" />
              </div>
              <div>
                <span className="section-kicker">用户管理</span>
                <h2>添加平台用户</h2>
                <p>只有管理员可以创建用户。普通用户将按学生权限访问知识库。</p>
              </div>
            </div>

            <form className="auth-form" onSubmit={(event) => void handleCreateUserSubmit(event)}>
              <label>
                用户名
                <input
                  value={newUsername}
                  onChange={(event) => setNewUsername(event.target.value)}
                  placeholder="例如 student001"
                  autoComplete="off"
                  required
                />
              </label>
              <label>
                显示名称
                <input
                  value={newDisplayName}
                  onChange={(event) => setNewDisplayName(event.target.value)}
                  placeholder="例如 张同学"
                  autoComplete="off"
                />
              </label>
              <label>
                角色
                <select value={newRole} onChange={(event) => setNewRole(event.target.value as 'student' | 'admin')}>
                  <option value="student">普通用户</option>
                  <option value="admin">管理员</option>
                </select>
              </label>
              <label>
                初始密码
                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  placeholder="至少 6 位"
                  autoComplete="new-password"
                  required
                />
              </label>

              {createUserError && <div className="auth-error">{createUserError}</div>}
              {createUserSuccess && <div className="auth-success">{createUserSuccess}</div>}

              <button className="auth-submit" type="submit" disabled={isCreateUserSubmitting}>
                {isCreateUserSubmitting ? '创建中...' : '创建用户'}
              </button>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
