import Vue from 'vue'
import { translate, translatePlural } from '@nextcloud/l10n'
import { generateUrl } from '@nextcloud/router'
import { APP_API_PROXY_URL_PREFIX, EX_APP_ID } from './constants/AppAPI.js'

Vue.prototype.t = translate
Vue.prototype.n = translatePlural
Vue.prototype.OC = window.OC
Vue.prototype.OCA = window.OCA

// eslint-disable-next-line
__webpack_public_path__ = generateUrl(`${APP_API_PROXY_URL_PREFIX}/${EX_APP_ID}/static/js/`)
