import PropTypes from 'prop-types';
import ConfigPanel from '../features/config/ConfigPanel.jsx';

export default function Header({ service }) {
  return (
    <header className="header">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
        <div>
          <div className="section-title">Current Service</div>
          <h2 style={{ margin: '0.25rem 0 0' }}>{service?.name ?? 'Select a service'}</h2>
          <p className="small-text" style={{ maxWidth: '720px', marginTop: '0.25rem' }}>
            {service?.description}
          </p>
        </div>
        <ConfigPanel />
      </div>
    </header>
  );
}

Header.propTypes = {
  service: PropTypes.shape({
    name: PropTypes.string,
    description: PropTypes.string
  })
};

Header.defaultProps = {
  service: null
};
