// PM2 Ecosystem Configuration for AutoCut Video
module.exports = {
  apps: [
    {
      name: "autocut-frontend",
      cwd: "/www/wwwroot/autocut-video/frontend",
      script: ".next/standalone/server.js",
      exec_mode: "fork",
      env: {
        NODE_ENV: "production",
        PORT: 3000,
        HOSTNAME: "127.0.0.1",
      },
      max_memory_restart: "512M",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      error_file: "/www/wwwroot/autocut-video/logs/frontend-error.log",
      out_file: "/www/wwwroot/autocut-video/logs/frontend-out.log",
      merge_logs: true,
    },
    {
      name: "autocut-backend",
      cwd: "/www/wwwroot/autocut-video/backend",
      script: "/www/wwwroot/autocut-video/start-backend.sh",
      interpreter: "/bin/bash",
      exec_mode: "fork",
      max_memory_restart: "512M",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      error_file: "/www/wwwroot/autocut-video/logs/backend-error.log",
      out_file: "/www/wwwroot/autocut-video/logs/backend-out.log",
      merge_logs: true,
    },
  ],
};
