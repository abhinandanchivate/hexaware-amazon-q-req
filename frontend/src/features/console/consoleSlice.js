import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  sessions: {}
};

const consoleSlice = createSlice({
  name: 'console',
  initialState,
  reducers: {
    setRequest(state, action) {
      const { key, body } = action.payload;
      if (!state.sessions[key]) {
        state.sessions[key] = { request: '', response: null, status: null, error: null, loading: false };
      }
      state.sessions[key].request = body;
    },
    setLoading(state, action) {
      const { key, loading } = action.payload;
      if (!state.sessions[key]) {
        state.sessions[key] = { request: '', response: null, status: null, error: null, loading: false };
      }
      state.sessions[key].loading = loading;
      if (loading) {
        state.sessions[key].error = null;
      }
    },
    setResponse(state, action) {
      const { key, response, status } = action.payload;
      if (!state.sessions[key]) {
        state.sessions[key] = { request: '', response: null, status: null, error: null, loading: false };
      }
      state.sessions[key].response = response;
      state.sessions[key].status = status;
      state.sessions[key].loading = false;
      state.sessions[key].error = null;
    },
    setError(state, action) {
      const { key, error, status } = action.payload;
      if (!state.sessions[key]) {
        state.sessions[key] = { request: '', response: null, status: null, error: null, loading: false };
      }
      state.sessions[key].error = error;
      state.sessions[key].status = status ?? null;
      state.sessions[key].loading = false;
    }
  }
});

export const { setRequest, setLoading, setResponse, setError } = consoleSlice.actions;
export default consoleSlice.reducer;
