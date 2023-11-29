import Vue from 'vue'
import Vuex, { Store } from 'vuex'

import example from './example.js'

Vue.use(Vuex)

export default new Store({
	modules: {
		example,
	},

	strict: process.env.NODE_ENV !== 'production',
})
