import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { setLoading, setResponse, setError } from '../console/consoleSlice.js';
import servicesData from './servicesData.js';

export const sendServiceRequest = createAsyncThunk(
  'services/sendRequest',
  async ({ serviceKey, endpointKey, body, params }, { getState, dispatch, rejectWithValue }) => {
    const {
      config: { baseUrl, token }
    } = getState();

    const sanitizedBase = baseUrl?.replace(/\/$/, '') ?? '';
    let urlString = endpointKey;
    if (!/^https?:/i.test(endpointKey)) {
      const prefix = sanitizedBase || (typeof window !== 'undefined' ? window.location.origin : '');
      const separator = endpointKey.startsWith('/') ? '' : '/';
      urlString = `${prefix}${separator}${endpointKey}`;
    }

    const url = new URL(urlString);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          url.searchParams.append(key, value);
        }
      });
    }

    const headers = {
      'Content-Type': 'application/json'
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const requestKey = `${serviceKey}${endpointKey}`;
    dispatch(setLoading({ key: requestKey, loading: true }));

    let payload;
    if (body && body.trim()) {
      try {
        payload = JSON.parse(body);
      } catch (parseError) {
        payload = body;
      }
    }

    try {
      const method = inferMethod(serviceKey, endpointKey);
      const requestConfig = {
        method,
        url: url.toString(),
        headers
      };

      if (payload !== undefined && method !== 'GET') {
        requestConfig.data = payload;
      }

      const response = await axios(requestConfig);
      dispatch(setResponse({ key: requestKey, response: response.data, status: response.status }));
      return response.data;
    } catch (error) {
      const status = error.response?.status;
      const payload = error.response?.data ?? error.message;
      dispatch(setError({ key: requestKey, error: payload, status }));
      return rejectWithValue({ status, payload });
    }
  }
);

function inferMethod(serviceKey, endpointKey) {
  const service = servicesData.find((item) => item.key === serviceKey);
  if (!service) return 'GET';
  const endpoint = service.endpoints.find((ep) => `${service.baseUrl}${ep.path}` === endpointKey || ep.fullPath === endpointKey);
  return endpoint?.method ?? 'GET';
}

const servicesSlice = createSlice({
  name: 'services',
  initialState: {
    catalog: servicesData,
    selectedService: servicesData[0]?.key ?? null,
    expandedEndpoints: {}
  },
  reducers: {
    selectService(state, action) {
      state.selectedService = action.payload;
    },
    toggleEndpoint(state, action) {
      const { serviceKey, endpointKey } = action.payload;
      const key = `${serviceKey}:${endpointKey}`;
      state.expandedEndpoints[key] = !state.expandedEndpoints[key];
    }
  }
});

export const { selectService, toggleEndpoint } = servicesSlice.actions;
export default servicesSlice.reducer;
