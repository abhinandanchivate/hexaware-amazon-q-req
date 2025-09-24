import PropTypes from 'prop-types';

const serviceOrder = [
  'hl7-parser',
  'patients',
  'observations',
  'appointments',
  'auth',
  'roles',
  'telemedicine',
  'notifications',
  'analytics',
  'audit',
  'fhir-gateway',
  'kafka'
];

export default function Sidebar({ services, selected, onSelect }) {
  const sorted = [...services].sort(
    (a, b) => serviceOrder.indexOf(a.key) - serviceOrder.indexOf(b.key)
  );

  return (
    <aside className="sidebar">
      <h1>FHIR Patient Portal</h1>
      <p className="small-text">Explore REST endpoints and event-driven contracts</p>
      <nav>
        {sorted.map((service) => (
          <button
            key={service.key}
            type="button"
            className={selected === service.key ? 'active' : ''}
            onClick={() => onSelect(service.key)}
          >
            {service.name}
          </button>
        ))}
      </nav>
      <div className="small-text">Built with React + Redux Toolkit</div>
    </aside>
  );
}

Sidebar.propTypes = {
  services: PropTypes.arrayOf(PropTypes.shape({ key: PropTypes.string.isRequired })).isRequired,
  selected: PropTypes.string,
  onSelect: PropTypes.func.isRequired
};

Sidebar.defaultProps = {
  selected: null
};
