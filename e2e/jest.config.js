module.exports = {
  preset: 'detox',
  setupFilesAfterEnv: ['<rootDir>/init.js'],
  testEnvironment: 'detox/runners/jest/testEnvironment',
  testMatch: ['<rootDir>/**/*.e2e.js'],
  collectCoverageFrom: [
    '**/*.{js,jsx}',
    '!**/*.e2e.js',
    '!**/node_modules/**',
  ],
  coverageReporters: ['text', 'lcov', 'html'],
  verbose: true,
};