import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'

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
		axios.post(generateUrl('/apps/app_api/proxy/ui_example/verify_initial_value'), {
			initial_value: value,
		})
			.then((res) => {
				if ('initial_value' in res.data) {
					context.commit('setInitialStateValue', res.data.initial_value)
				}
				showSuccess(this.t('ui_example', 'Initial value is correct'))
			})
			.catch(() => showError(this.t('ui_example', 'Initial value is incorrect')))
	},
}

export default { state, mutations, getters, actions }
