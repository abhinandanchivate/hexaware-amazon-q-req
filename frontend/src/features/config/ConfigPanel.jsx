import { useDispatch, useSelector } from 'react-redux';
import { useState } from 'react';
import { setBaseUrl, setToken, setKafkaBootstrap } from './configSlice.js';

export default function ConfigPanel() {
  const dispatch = useDispatch();
  const { baseUrl, token, kafkaBootstrap } = useSelector((state) => state.config);
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card" style={{ minWidth: '320px', padding: '1rem' }}>
      <button type="button" className="secondary" onClick={() => setExpanded((state) => !state)}>
        {expanded ? 'Hide environment' : 'Show environment'}
      </button>
      {expanded ? (
        <div className="panel-stack" style={{ marginTop: '1rem' }}>
          <label className="small-text" htmlFor="config-base-url">
            Base API URL
          </label>
          <input
            id="config-base-url"
            type="text"
            value={baseUrl}
            onChange={(event) => dispatch(setBaseUrl(event.target.value))}
            style={{ padding: '0.5rem', borderRadius: '0.5rem', border: '1px solid #cbd5f5' }}
          />
          <label className="small-text" htmlFor="config-token">
            Bearer token
          </label>
          <input
            id="config-token"
            type="text"
            value={token}
            onChange={(event) => dispatch(setToken(event.target.value))}
            style={{ padding: '0.5rem', borderRadius: '0.5rem', border: '1px solid #cbd5f5' }}
          />
          <label className="small-text" htmlFor="config-kafka">
            Kafka bootstrap servers
          </label>
          <input
            id="config-kafka"
            type="text"
            value={kafkaBootstrap}
            onChange={(event) => dispatch(setKafkaBootstrap(event.target.value))}
            style={{ padding: '0.5rem', borderRadius: '0.5rem', border: '1px solid #cbd5f5' }}
          />
        </div>
      ) : null}
    </div>
  );
}
