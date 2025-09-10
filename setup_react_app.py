#!/usr/bin/env python3
"""
Quick setup script for React HR frontend
"""

import os
import json

def create_file(path, content):
    """Create a file with given content"""
    dirname = os.path.dirname(path)
    if dirname:  # Only create directory if it's not empty
        os.makedirs(dirname, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created {path}")

def setup_react_app():
    """Set up the complete React app structure"""
    
    print("🚀 Setting up React HR Frontend...")
    
    # Create src directory
    os.makedirs('src', exist_ok=True)
    
    # Package.json
    package_json = {
        "name": "hr-mcp-frontend",
        "private": True,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
            "preview": "vite preview",
            "start": "vite"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        },
        "devDependencies": {
            "@types/react": "^18.2.43",
            "@types/react-dom": "^18.2.17",
            "@typescript-eslint/eslint-plugin": "^6.14.0",
            "@typescript-eslint/parser": "^6.14.0",
            "@vitejs/plugin-react": "^4.2.1",
            "eslint": "^8.55.0",
            "eslint-plugin-react-hooks": "^4.6.0",
            "eslint-plugin-react-refresh": "^0.4.5",
            "typescript": "^5.2.2",
            "vite": "^7.0.6"
        }
    }
    
    with open('package.json', 'w') as f:
        json.dump(package_json, f, indent=2)
    print("✅ Created package.json")
    
    # Vite config
    vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  }
})'''
    create_file('vite.config.ts', vite_config)
    
    # TSConfig
    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True
        },
        "include": ["src"],
        "references": [{"path": "./tsconfig.node.json"}]
    }
    
    with open('tsconfig.json', 'w') as f:
        json.dump(tsconfig, f, indent=2)
    print("✅ Created tsconfig.json")
    
    # TSConfig Node
    tsconfig_node = {
        "compilerOptions": {
            "composite": True,
            "skipLibCheck": True,
            "module": "ESNext",
            "moduleResolution": "bundler",
            "allowSyntheticDefaultImports": True,
            "strict": True
        },
        "include": ["vite.config.ts"]
    }
    
    with open('tsconfig.node.json', 'w') as f:
        json.dump(tsconfig_node, f, indent=2)
    print("✅ Created tsconfig.node.json")
    
    # Index.html
    index_html = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>HR Self-Service Portal</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''
    create_file('index.html', index_html)
    
    # Main.tsx
    main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
    create_file('src/main.tsx', main_tsx)
    
    # App.tsx - Basic version to start
    app_tsx = '''import React, { useState, useEffect } from 'react';
import './App.css';

const App: React.FC = () => {
  const [message, setMessage] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'websocket' | 'http'>('disconnected');

  useEffect(() => {
    // Test WebSocket connection
    try {
      const ws = new WebSocket('ws://localhost:8765');
      ws.onopen = () => {
        setConnectionStatus('websocket');
        ws.close();
      };
      ws.onerror = () => {
        setConnectionStatus('disconnected');
      };
    } catch {
      setConnectionStatus('disconnected');
    }
  }, []);

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'websocket': return '🟢 MCP Bridge Connected';
      case 'http': return '🟡 HTTP Fallback';
      case 'disconnected': return '🔴 MCP Bridge Offline';
    }
  };

  return (
    <div className="hr-app">
      <header className="header">
        <div className="header-content">
          <h1>🏢 HR Self-Service Portal</h1>
          <p>Submit leave requests and expense claims via MCP</p>
          <div className="connection-status">
            {getConnectionStatusText()}
          </div>
        </div>
      </header>

      <main className="main">
        <div className="form-card">
          <h2>Welcome to your HR Portal!</h2>
          <p>The frontend is running. Now start your MCP bridge:</p>
          <div className="instructions">
            <h3>Next Steps:</h3>
            <ol>
              <li>Open a new terminal</li>
              <li>Run: <code>python mcp_websocket_bridge.py</code></li>
              <li>Refresh this page</li>
              <li>Start submitting HR requests!</li>
            </ol>
          </div>
          
          {connectionStatus === 'websocket' && (
            <div className="success-banner">
              ✅ MCP Bridge is connected! The full functionality is available.
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>Powered by your MCP server + n8n workflows</p>
      </footer>
    </div>
  );
};

export default App;'''
    create_file('src/App.tsx', app_tsx)
    
    # Basic App.css
    app_css = '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: #333;
}

.hr-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  text-align: center;
  padding: 2rem;
  color: white;
}

.header-content h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.connection-status {
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  display: inline-block;
  margin-top: 1rem;
}

.main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.form-card {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
  text-align: center;
}

.instructions {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 12px;
  margin: 1rem 0;
  text-align: left;
}

.instructions ol {
  margin-top: 1rem;
  padding-left: 1.5rem;
}

.instructions li {
  margin-bottom: 0.5rem;
}

.instructions code {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.success-banner {
  background: #d4edda;
  color: #155724;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #c3e6cb;
  margin-top: 1rem;
}

.footer {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  text-align: center;
  padding: 1rem;
  color: white;
}'''
    create_file('src/App.css', app_css)
    
    # Index.css
    index_css = ''':root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

#root {
  width: 100%;
  margin: 0;
}'''
    create_file('src/index.css', index_css)
    
    print("\n🎉 React app setup complete!")
    print("\n📋 Next steps:")
    print("1. Run: npm install")
    print("2. Run: npm run dev")
    print("3. In another terminal: python mcp_websocket_bridge.py")
    print("4. Visit: http://localhost:5173")

if __name__ == "__main__":
    setup_react_app()