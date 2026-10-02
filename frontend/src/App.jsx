import './App.css';
import MainLayout from './components/MainLayout';
import ProductSearchPage from './pages/ProductSearchPage';

function App() {
  return <MainLayout>{(onSearchChange) => <ProductSearchPage onSearchChange={onSearchChange} />}</MainLayout>;
}

export default App;