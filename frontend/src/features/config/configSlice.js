import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  baseUrl: 'http://localhost:8000',
  token: '',
  kafkaBootstrap: 'kafka://localhost:9092'
};

const configSlice = createSlice({
  name: 'config',
  initialState,
  reducers: {
    setBaseUrl(state, action) {
      state.baseUrl = action.payload;
    },
    setToken(state, action) {
      state.token = action.payload;
    },
    setKafkaBootstrap(state, action) {
      state.kafkaBootstrap = action.payload;
    },
    resetConfig() {
      return initialState;
    }
  }
});

export const { setBaseUrl, setToken, setKafkaBootstrap, resetConfig } = configSlice.actions;
export default configSlice.reducer;
