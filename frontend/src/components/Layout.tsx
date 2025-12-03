import { Outlet, Link, useLocation } from 'react-router-dom';
import { useConnectionStore } from '@/stores/connectionStore';
import { ConnectionStatus } from '@/types';

const Layout = () => {
  const location = useLocation();
  const { status } = useConnectionStore();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const getConnectionStatusColor = () => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return 'bg-green-500';
      case ConnectionStatus.CONNECTING:
      case ConnectionStatus.RECONNECTING:
        return 'bg-yellow-500';
      case ConnectionStatus.ERROR:
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getConnectionStatusText = () => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return 'Connected';
      case ConnectionStatus.CONNECTING:
        return 'Connecting...';
      case ConnectionStatus.RECONNECTING:
        return 'Reconnecting...';
      case ConnectionStatus.ERROR:
        return 'Connection Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center font-bold text-xl">
                911
              </div>
              <div>
                <h1 className="text-2xl font-bold">Operator Training Simulator</h1>
                <p className="text-sm text-blue-200">AI-Powered Emergency Response Training</p>
              </div>
            </div>

            {/* Connection Status */}
            <div className="flex items-center space-x-2 bg-blue-800 px-4 py-2 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${getConnectionStatusColor()} animate-pulse`} />
              <span className="text-sm font-medium">{getConnectionStatusText()}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-md border-b">
        <div className="container mx-auto px-4">
          <ul className="flex space-x-8">
            <li>
              <Link
                to="/scenarios"
                className={`block py-4 border-b-2 transition-colors ${
                  isActive('/scenarios')
                    ? 'border-blue-600 text-blue-600 font-semibold'
                    : 'border-transparent text-gray-600 hover:text-blue-600 hover:border-gray-300'
                }`}
              >
                Scenarios
              </Link>
            </li>
            <li>
              <Link
                to="/dashboard"
                className={`block py-4 border-b-2 transition-colors ${
                  isActive('/dashboard')
                    ? 'border-blue-600 text-blue-600 font-semibold'
                    : 'border-transparent text-gray-600 hover:text-blue-600 hover:border-gray-300'
                }`}
              >
                Active Call
              </Link>
            </li>
            <li>
              <Link
                to="/history"
                className={`block py-4 border-b-2 transition-colors ${
                  isActive('/history')
                    ? 'border-blue-600 text-blue-600 font-semibold'
                    : 'border-transparent text-gray-600 hover:text-blue-600 hover:border-gray-300'
                }`}
              >
                Call History
              </Link>
            </li>
          </ul>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-300 py-6">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">
            &copy; 2025 911 Operator Training Simulator. All rights reserved.
          </p>
          <p className="text-xs mt-2 text-gray-400">
            Powered by AI | For Training Purposes Only
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
