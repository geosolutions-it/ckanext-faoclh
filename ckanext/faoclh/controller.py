import ckan.lib.base as base

class VocabController(base.BaseController):
    def get(self):
        return base.render('admin/vocabs.html')