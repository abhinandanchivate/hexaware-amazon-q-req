import { useDispatch, useSelector } from 'react-redux';
import PropTypes from 'prop-types';
import { useMemo } from 'react';
import { setRequest } from '../features/console/consoleSlice.js';
import { sendServiceRequest, toggleEndpoint } from '../features/services/servicesSlice.js';

export default function EndpointCard({ service, endpoint }) {
  const dispatch = useDispatch();
  const expanded = useSelector((state) => state.services.expandedEndpoints[`${service.key}:${endpoint.id}`]);
  const sessionKey = `${service.key}${endpoint.fullPath}`;
  const sessionState = useSelector((state) => state.console.sessions[sessionKey]);
  const requestBody = sessionState?.request ?? endpoint.requestPayload ?? '';
  const loading = sessionState?.loading ?? false;
  const response = sessionState?.response;
  const error = sessionState?.error;
  const status = sessionState?.status;

  const methodClass = useMemo(() => `method-pill method-${endpoint.method}`, [endpoint.method]);

  const isExecutable = endpoint.method !== 'DESIGN';

  const handleExecute = () => {
    if (!isExecutable) {
      return;
    }
    dispatch(sendServiceRequest({
      serviceKey: service.key,
      endpointKey: endpoint.fullPath,
      body: requestBody,
      params: undefined
    }));
  };

  const handleReset = () => {
    dispatch(
      setRequest({
        key: sessionKey,
        body: endpoint.requestPayload ?? ''
      })
    );
  };

  return (
    <div className="endpoint-card">
      <div className="endpoint-header">
        <span className={methodClass}>{endpoint.method}</span>
        <div>
          <strong>{endpoint.name}</strong>
          <div className="small-text">{endpoint.summary}</div>
          <div className="small-text">{endpoint.fullPath}</div>
        </div>
      </div>

      {endpoint.requestHeaders?.length ? (
        <div className="panel-stack">
          <div className="section-title">Headers</div>
          <div className="table-like">
            {endpoint.requestHeaders.map((header) => (
              <div className="row" key={header.key}>
                <span className="label">{header.key}</span>
                <span>{header.value}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {endpoint.validationRules?.length ? (
        <div className="panel-stack">
          <div className="section-title">Validation Rules</div>
          <ul className="small-text" style={{ margin: 0 }}>
            {endpoint.validationRules.map((rule) => (
              <li key={rule}>{rule}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {endpoint.kafkaEvents?.length ? (
        <div className="panel-stack">
          <div className="section-title">Kafka Events</div>
          <div className="tag-list">
            {endpoint.kafkaEvents.map((topic) => (
              <span className="tag" key={topic}>
                {topic}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {endpoint.queryParameters?.length ? (
        <div className="panel-stack">
          <div className="section-title">Query Parameters</div>
          <div className="tag-list">
            {endpoint.queryParameters.map((param) => (
              <span className="tag" key={param}>
                {param}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {endpoint.requestPayload ? (
        <div className="panel-stack">
          <div className="section-title">Sample Request</div>
          <textarea
            className="json-input"
            value={requestBody}
            onChange={(event) =>
              dispatch(
                setRequest({
                  key: sessionKey,
                  body: event.target.value
                })
              )
            }
          />
          <div className="button-row">
            {isExecutable ? (
              <button type="button" className="primary" onClick={handleExecute} disabled={loading}>
                {loading ? 'Sending…' : 'Send Request'}
              </button>
            ) : null}
            <button type="button" className="secondary" onClick={handleReset}>
              Reset sample
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => dispatch(toggleEndpoint({ serviceKey: service.key, endpointKey: endpoint.id }))}
            >
              {expanded ? 'Hide Response' : 'Show Response'}
            </button>
          </div>
        </div>
      ) : (
        <div className="button-row">
          {isExecutable ? (
            <button type="button" className="primary" onClick={handleExecute} disabled={loading}>
              {loading ? 'Sending…' : 'Send Request'}
            </button>
          ) : null}
          <button
            type="button"
            className="secondary"
            onClick={() => dispatch(toggleEndpoint({ serviceKey: service.key, endpointKey: endpoint.id }))}
          >
            {expanded ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
      )}

      {expanded && (response || error || endpoint.responsePayload) ? (
        <div className="panel-stack">
          <div className="section-title">Response</div>
          {status ? <div className="badge">HTTP {status}</div> : null}
          {error ? (
            <div className="alert">
              <strong>Request failed:</strong>
              <pre className="code-block" style={{ marginTop: '0.5rem' }}>
                {typeof error === 'string' ? error : JSON.stringify(error, null, 2)}
              </pre>
            </div>
          ) : response ? (
            <pre className="code-block">{JSON.stringify(response, null, 2)}</pre>
          ) : (
            <pre className="code-block">{endpoint.responsePayload ?? 'No response example available.'}</pre>
          )}
        </div>
      ) : null}
    </div>
  );
}

EndpointCard.propTypes = {
  service: PropTypes.shape({ key: PropTypes.string.isRequired }).isRequired,
  endpoint: PropTypes.shape({
    id: PropTypes.string.isRequired,
    method: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    summary: PropTypes.string,
    fullPath: PropTypes.string
  }).isRequired
};
