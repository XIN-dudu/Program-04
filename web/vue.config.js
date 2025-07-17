module.exports = {
  transpileDependencies: true,
  lintOnSave: false,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: { '^/api': '/api' }
      },
      '/road': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: { '^/road': '/road' }
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // 不需要pathRewrite，直接转发
      }
    }
  }
}