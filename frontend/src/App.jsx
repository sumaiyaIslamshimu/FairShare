import { useState, useEffect } from 'react';
import './App.css';
import MainLayout from './components/MainLayout';
import ProductSearchPage from './pages/ProductSearchPage';
import RentalRequestsScreen from './pages/RentalRequestsScreen';
import ListingForm from './components/ListingForm';

function App() {
  const [currentRoute, setCurrentRoute] = useState(window.location.hash || '');

  useEffect(() => {
    const handleHashChange = () => setCurrentRoute(window.location.hash);
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const renderContent = (onSearchChange) => {
    switch (currentRoute) {
      case '#rental-requests':
        return <RentalRequestsScreen />;
      case '#create-listing':
        return <ListingForm />;
      default:
        // Defaults to Search & Browse
        return <ProductSearchPage onSearchChange={onSearchChange} />;
    }
  };

  return (
    <MainLayout>
      {(onSearchChange) => renderContent(onSearchChange)}
    </MainLayout>
  );
}

export default App;