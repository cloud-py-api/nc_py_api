import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import { APP_API_PROXY_URL_PREFIX, EX_APP_ID } from '../constants/AppAPI.js'
import { translate as t } from '@nextcloud/l10n'

const state = {
	initial_state_value: {},
}

const mutations = {
	setInitialStateValue(state, data) {
		state.initial_state_value = data
	},
}

const getters = {
	getInitialStateValue: (state) => state.initial_state_value,
}

const actions = {
	verifyInitialStateValue(context, value) {
		axios.post(generateUrl(`${APP_API_PROXY_URL_PREFIX}/${EX_APP_ID}/verify_initial_value`), {
			initial_value: value,
		})
			.then((res) => {
				if ('initial_value' in res.data) {
					context.commit('setInitialStateValue', res.data.initial_value)
				} else {
					context.commit('setInitialStateValue', { error: 'No initial value returned' })
				}
				showSuccess(t('ui_example', 'Initial value is correct'))
			})
			.catch(() => {
				context.commit('setInitialStateValue', { error: 'Initial value is incorrect' })
				showError(t('ui_example', 'Initial value is incorrect'))
			})
	},
}

export default { state, mutations, getters, actions }
