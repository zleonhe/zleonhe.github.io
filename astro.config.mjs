import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://eda.cs.tsinghua.edu.cn',
  base: '/~zlhe/',
  output: 'static',
  trailingSlash: 'always',
});
