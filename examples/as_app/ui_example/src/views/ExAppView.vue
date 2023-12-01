<template>
	<div class="ui-example">
		<h2>{{ t('ui_example', 'ExApp UI example') }}</h2>
		<p>{{ t('ui_example', 'All front-end stuff kept the same for seamless migration for developers. All needed stuff is proxying via AppAPI') }}</p>
		<NcInputField :value="initialState?.initial_value" :label="t('ui_example', 'Initial value')" :disabled="true" />
		<p>
			{{ t('ui_example', 'Initial value from store') }}: {{ initialStateValue }}
		</p>
		<NcButton @click="verifyInitialValue">
			{{ t('ui_example', 'Verify initial value') }}
		</NcButton>
	</div>
</template>

<script>
import { loadState } from '@nextcloud/initial-state'
import NcInputField from '@nextcloud/vue/dist/Components/NcInputField.js'
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'

export default {
	name: 'ExAppView',
	components: {
		NcInputField,
		NcButton,
	},
	data() {
		return {
			initialState: JSON.parse(loadState('app_api', 'ui_example_state')),
		}
	},
	computed: {
		initialStateValue() {
			return this.$store.getters.getInitialStateValue
		},
	},
	methods: {
		verifyInitialValue() {
			this.$store.dispatch('verifyInitialStateValue', this.initialState?.initial_value)
		},
	},
}
</script>

<style lang="scss" scoped>
.ui-example {
	width: 100%;
	max-width: 600px;
	display: flex;
	flex-direction: column;
	align-items: center;
	margin: 0 auto;
	padding: 30px;

	input, p {
		margin: 20px 0;
	}
}
</style>
