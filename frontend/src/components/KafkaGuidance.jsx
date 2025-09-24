import PropTypes from 'prop-types';

export default function KafkaGuidance({ endpoints }) {
  return (
    <div className="grid">
      {endpoints.map((endpoint) => (
        <div key={endpoint.id} className="endpoint-card">
          <div className="endpoint-header">
            <span className="method-pill method-DESIGN">KAFKA</span>
            <div>
              <strong>{endpoint.name}</strong>
              <div className="small-text">{endpoint.summary}</div>
            </div>
          </div>
          <pre className="code-block">{endpoint.responsePayload}</pre>
        </div>
      ))}
    </div>
  );
}

KafkaGuidance.propTypes = {
  endpoints: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      summary: PropTypes.string,
      responsePayload: PropTypes.string
    })
  ).isRequired
};
