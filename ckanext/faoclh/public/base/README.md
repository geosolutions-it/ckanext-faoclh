# Generate CSS from custom less

Steps to update main.css file with less:

- update the variable `@ckan-less-dir-path` in the `less/main.less` file with the correct path to less directory of ckan eg: `/path/to/ckan/ckan/public/base/less/`

- install needed packages with `npm install`

- change less style inside `less/custom.less` file

- update `css/main.css` with the command `npm run generate-less`

---

Required:

- node v8.3.0

- npm  v5.3.0