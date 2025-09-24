import { useDispatch, useSelector } from 'react-redux';
import { useMemo } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Header from './components/Header.jsx';
import ServiceContent from './components/ServiceContent.jsx';
import { selectService } from './features/services/servicesSlice.js';

export default function App() {
  const dispatch = useDispatch();
  const services = useSelector((state) => state.services.catalog);
  const selectedService = useSelector((state) => state.services.selectedService);

  const currentService = useMemo(
    () => services.find((service) => service.key === selectedService) ?? services[0],
    [services, selectedService]
  );

  return (
    <div className="app-shell">
      <Sidebar
        services={services}
        selected={selectedService}
        onSelect={(key) => dispatch(selectService(key))}
      />
      <div className="main-area">
        <Header service={currentService} />
        <ServiceContent service={currentService} />
      </div>
    </div>
  );
}
