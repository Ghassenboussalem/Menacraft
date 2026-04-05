import { useStore } from './store/useStore.js';
import Sidebar from './components/Sidebar.jsx';
import ConfigModal from './components/ConfigModal.jsx';
import PostModal from './components/PostModal.jsx';
import ToastContainer from './components/Toast.jsx';
import FeedScreen from './screens/FeedScreen.jsx';
import ArchitectureScreen from './screens/ArchitectureScreen.jsx';
import ErrorBoundary from './components/ErrorBoundary.jsx';

export default function App() {
  const view = useStore((s) => s.view);

  return (
    <ErrorBoundary>
      <Sidebar />
      <div className="main">
        {view === 'feed' ? <FeedScreen /> : <ArchitectureScreen />}
      </div>
      <ConfigModal />
      <ErrorBoundary>
        <PostModal />
      </ErrorBoundary>
      <ToastContainer />
    </ErrorBoundary>
  );
}
