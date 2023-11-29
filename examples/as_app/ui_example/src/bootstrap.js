import Vue from 'vue'
import { translate, translatePlural } from '@nextcloud/l10n'
import { generateFilePath } from '@nextcloud/router'
// import { EX_APP_ID } from './constants/AppAPI'

Vue.prototype.t = translate
Vue.prototype.n = translatePlural
Vue.prototype.OC = window.OC
Vue.prototype.OCA = window.OCA

// eslint-disable-next-line
__webpack_public_path__ = generateFilePath('app_api', '', 'js/')
// TODO: Figure out about which path to use here (proxy or app_api)
// __webpack_public_path__ = generateFilePath(EX_APP_ID, '', 'js/')
