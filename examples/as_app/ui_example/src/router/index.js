import VueRouter from 'vue-router' // eslint-disable-line
import { generateUrl } from '@nextcloud/router'
import Vue from 'vue'
import { APP_API_PROXY_URL_PREFIX, EX_APP_ID } from '../constants/AppAPI.js'

const ExAppView = () => import('../views/ExAppView.vue')

Vue.use(VueRouter)

function setPageHeading(heading) {
	const headingEl = document.getElementById('page-heading-level-1')
	if (headingEl) {
		headingEl.textContent = heading
	}
}

const baseTitle = document.title
const router = new VueRouter({
	mode: 'history',
	base: generateUrl(`${APP_API_PROXY_URL_PREFIX}/${EX_APP_ID}`, ''), // setting base to AppAPI proxy URL
	linkActiveClass: 'active',
	routes: [
		{
			path: '/',
			component: ExAppView,
			name: 'ui_example_index',
			meta: {
				title: async () => {
					return t('app_api', 'ExApp UI Example')
				},
			},
		},
	],
})

router.afterEach(async (to) => {
	const metaTitle = await to.meta.title?.(to)
	if (metaTitle) {
		document.title = `${metaTitle} - ${baseTitle}`
		setPageHeading(metaTitle)
	} else {
		document.title = baseTitle
	}
})

export default router
