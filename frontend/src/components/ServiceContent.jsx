import PropTypes from 'prop-types';
import EndpointCard from './EndpointCard.jsx';
import KafkaGuidance from './KafkaGuidance.jsx';

export default function ServiceContent({ service }) {
  if (!service) {
    return (
      <main className="content">
        <div className="card">Select a service to explore its endpoints.</div>
      </main>
    );
  }

  const isKafka = service.key === 'kafka';

  return (
    <main className="content">
      <div className="card">
        <div className="section-title">Base URL</div>
        <div className="badge">{service.baseUrl || 'Documentation'}</div>
      </div>

      {isKafka ? (
        <KafkaGuidance endpoints={service.endpoints} />
      ) : (
        <div className="grid">
          {service.endpoints.map((endpoint) => (
            <EndpointCard key={endpoint.id} service={service} endpoint={endpoint} />
          ))}
        </div>
      )}
    </main>
  );
}

ServiceContent.propTypes = {
  service: PropTypes.shape({
    key: PropTypes.string,
    baseUrl: PropTypes.string,
    endpoints: PropTypes.arrayOf(PropTypes.object)
  })
};

ServiceContent.defaultProps = {
  service: null
};
