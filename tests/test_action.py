from collections import OrderedDict
import unittest
from unittest.mock import patch, call
from homu import action
from homu.action import LabelEvent


TRY_CHOOSER_CONFIG = {
    "buildbot": {
        "builders": ["mac-rel", "mac-wpt", "linux-wpt-1", "linux-wpt-2"],
        # keeps the order for testing output
        "try_choosers": OrderedDict([
            ("mac", ["mac-rel", "mac-wpt"]),
            ("wpt", ["linux-wpt-1", "linux-wpt-2"])
        ])
    }
}

class TestAction(unittest.TestCase):

    @patch('homu.main.PullReqState')
    @patch('homu.action.get_portal_turret_dialog', return_value='message')
    def test_still_here(self, mock_message, MockPullReqState):
        state = MockPullReqState()
        action.still_here(state)
        state.add_comment.assert_called_once_with(':cake: message\n\n![](https://cloud.githubusercontent.com/assets/1617736/22222924/c07b2a1c-e16d-11e6-91b3-ac659550585c.png)')

    @patch('homu.main.PullReqState')
    def test_set_treeclosed(self, MockPullReqState):
        state = MockPullReqState()
        action.set_treeclosed(state, '123')
        state.change_treeclosed.assert_called_once_with(123)
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_delegate_to(self, MockPullReqState):
        state = MockPullReqState()
        action.delegate_to(state, True, 'user')
        self.assertEqual(state.delegate, 'user')
        state.save.assert_called_once_with()
        state.add_comment.assert_called_once_with(
            ':v: @user can now approve this pull request'
        )

    @patch('homu.main.PullReqState')
    def test_hello_or_ping(self, MockPullReqState):
        state = MockPullReqState()
        action.hello_or_ping(state)
        state.add_comment.assert_called_once_with(":sleepy: I'm awake I'm awake")

    @patch('homu.main.PullReqState')
    def test_rollup_positive(self, MockPullReqState):
        state = MockPullReqState()
        action.rollup(state, 'rollup')
        self.assertTrue(state.rollup)
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_rollup_negative(self, MockPullReqState):
        state = MockPullReqState()
        action.rollup(state, 'rollup-')
        self.assertFalse(state.rollup)
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_try_positive(self, MockPullReqState):
        state = MockPullReqState()
        action._try(state, 'try', False, {})
        self.assertTrue(state.try_)
        state.init_build_res.assert_called_once_with([])
        state.save.assert_called_once_with()
        state.change_labels.assert_called_once_with(LabelEvent.TRY)

    @patch('homu.main.PullReqState')
    def test_try_negative(self, MockPullReqState):
        state = MockPullReqState()
        action._try(state, 'try-', False, {})
        self.assertFalse(state.try_)
        state.init_build_res.assert_called_once_with([])
        state.save.assert_called_once_with()
        assert not state.change_labels.called, 'change_labels was called and should never be.'

    @patch('homu.main.PullReqState')
    def test_try_chooser_no_setup(self, MockPullReqState):
        state = MockPullReqState()
        action._try(state, 'try', True, {}, choose="foo")
        self.assertTrue(state.try_)
        state.init_build_res.assert_called_once_with([])
        state.save.assert_called_once_with()
        state.change_labels.assert_called_once_with(LabelEvent.TRY)
        state.add_comment.assert_called_once_with(":slightly_frowning_face: This repo does not have try choosers set up")

    @patch('homu.main.PullReqState')
    def test_try_chooser_not_found(self, MockPullReqState):
        state = MockPullReqState()
        action._try(state, 'try', True, TRY_CHOOSER_CONFIG, choose="foo")
        self.assertEqual(state.try_choose, None)
        state.init_build_res.assert_not_called()
        state.save.assert_not_called()
        state.change_labels.assert_not_called()
        state.add_comment.assert_called_once_with(":slightly_frowning_face: There is no try chooser foo for this repo, try one of: mac, wpt")

    @patch('homu.main.PullReqState')
    def test_try_chooser_found(self, MockPullReqState):
        state = MockPullReqState()
        action._try(state, 'try', True, TRY_CHOOSER_CONFIG, choose="mac")
        self.assertTrue(state.try_)
        self.assertEqual(state.try_choose, "mac")
        state.init_build_res.assert_called_once_with([])
        state.save.assert_called_once_with()
        state.change_labels.assert_called_once_with(LabelEvent.TRY)

    @patch('homu.main.PullReqState')
    def test_clean(self, MockPullReqState):
        state = MockPullReqState()
        action.clean(state)
        self.assertEqual(state.merge_sha, '')
        state.init_build_res.assert_called_once_with([])
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_retry_try(self, MockPullReqState):
        state = MockPullReqState()
        state.try_ = True
        action.retry(state)
        state.set_status.assert_called_once_with('')
        state.change_labels.assert_called_once_with(LabelEvent.TRY)

    @patch('homu.main.PullReqState')
    def test_treeclosed_negative(self, MockPullReqState):
        state = MockPullReqState()
        action.treeclosed_negative(state)
        state.change_treeclosed.assert_called_once_with(-1)
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_retry_approved(self, MockPullReqState):
        state = MockPullReqState()
        state.try_ = False
        action.retry(state)
        state.set_status.assert_called_once_with('')
        state.change_labels.assert_called_once_with(LabelEvent.APPROVED)

    @patch('homu.main.PullReqState')
    def test_delegate_negative(self, MockPullReqState):
        state = MockPullReqState()
        state.delegate = 'delegate'
        action.delegate_negative(state)
        self.assertEqual(state.delegate, '')
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_delegate_positive_realtime(self, MockPullReqState):
        state = MockPullReqState()
        action.delegate_positive(state, 'delegate', True)
        self.assertEqual(state.delegate, 'delegate')
        state.add_comment.assert_called_once_with(':v: @delegate can now approve this pull request')
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_delegate_positive_not_realtime(self, MockPullReqState):
        state = MockPullReqState()
        action.delegate_positive(state, 'delegate', False)
        self.assertEqual(state.delegate, 'delegate')
        state.save.assert_called_once_with()
        assert not state.add_comment.called, 'state.save was called and should never be.'

    @patch('homu.main.PullReqState')
    def test_set_priority_not_priority_less_than_max_priority(self, MockPullReqState):
        state = MockPullReqState()
        action.set_priority(state, True, '1', {'max_priority': 3})
        self.assertEqual(state.priority, 1)
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_set_priority_not_priority_more_than_max_priority(self, MockPullReqState):
        state = MockPullReqState()
        state.priority = 2
        self.assertFalse(action.set_priority(state, True, '5', {'max_priority': 3}))
        self.assertEqual(state.priority, 2)
        state.add_comment.assert_called_once_with(':stop_sign: Priority higher than 3 is ignored.')
        assert not state.save.called, 'state.save was called and should never be.'

    @patch('homu.main.PullReqState')
    def test_review_approved_approver_me(self, MockPullReqState):
        state = MockPullReqState()
        self.assertFalse(action.review_approved(state, True, 'me', 'user', 'user', '', []))

    @patch('homu.main.PullReqState')
    def test_review_approved_wip_todo_realtime(self, MockPullReqState):
        state = MockPullReqState()
        state.title = 'WIP work in progress'
        self.assertFalse(action.review_approved(state, True, 'user', 'user', 'user', '', []))
        state.add_comment.assert_called_once_with(':clipboard: Looks like this PR is still in progress, ignoring approval')

    @patch('homu.main.PullReqState')
    def test_review_approved_wip_not_realtime(self, MockPullReqState):
        state = MockPullReqState()
        state.title = 'WIP work in progress'
        self.assertFalse(action.review_approved(state, False, 'user', 'user', 'user', '', []))
        assert not state.add_comment.called, 'state.add_comment was called and should never be.'

    @patch('homu.main.PullReqState')
    def test_review_approved_equal_usernames(self, MockPullReqState):
        state = MockPullReqState()
        state.head_sha = 'abcd123'
        state.title = "My pull request"
        self.assertTrue(action.review_approved(state, True, 'user' ,'user', 'user', 'abcd123', []))
        self.assertEqual(state.approved_by, 'user')
        self.assertFalse(state.try_)
        state.set_status.assert_called_once_with('')
        state.save.assert_called_once_with()

    @patch('homu.main.PullReqState')
    def test_review_approved_different_usernames_sha_equals_head_sha(self, MockPullReqState):
        state = MockPullReqState()
        state.head_sha = 'abcd123'
        state.title = "My pull request"
        state.repo_label = 'label'
        state.status = 'pending'
        states = {}
        states[state.repo_label] = {'label': state}
        self.assertTrue(action.review_approved(state, True, 'user1' ,'user1', 'user2', 'abcd123', states))
        self.assertEqual(state.approved_by, 'user1')
        self.assertFalse(state.try_)
        state.set_status.assert_called_once_with('')
        state.save.assert_called_once_with()
        state.add_comment.assert_called_once_with(":bulb: This pull request was already approved, no need to approve it again.\n\n- This pull request is currently being tested. If there's no response from the continuous integration service, you may use `retry` to trigger a build again.")

    @patch('homu.main.PullReqState')
    def test_review_approved_different_usernames_sha_different_head_sha(self, MockPullReqState):
        state = MockPullReqState()
        state.head_sha = 'sdf456'
        state.title = "My pull request"
        state.repo_label = 'label'
        state.status = 'pending'
        state.num = 1
        states = {}
        states[state.repo_label] = {'label': state}
        self.assertTrue(action.review_approved(state, True, 'user1', 'user1', 'user2', 'abcd123', states))
        state.add_comment.assert_has_calls([call(":bulb: This pull request was already approved, no need to approve it again.\n\n- This pull request is currently being tested. If there's no response from the continuous integration service, you may use `retry` to trigger a build again."),
                                            call(':scream_cat: `abcd123` is not a valid commit SHA. Please try again with `sdf456`.')])

    @patch('homu.main.PullReqState')
    def test_review_approved_different_usernames_blank_sha_not_blocked_by_closed_tree(self, MockPullReqState):
        state = MockPullReqState()
        state.blocked_by_closed_tree.return_value = 0
        state.head_sha = 'sdf456'
        state.title = "My pull request"
        state.repo_label = 'label'
        state.status = 'pending'
        states = {}
        states[state.repo_label] = {'label': state}
        self.assertTrue(action.review_approved(state, True, 'user1', 'user1', 'user2', '', states))
        state.add_comment.assert_has_calls([call(":bulb: This pull request was already approved, no need to approve it again.\n\n- This pull request is currently being tested. If there's no response from the continuous integration service, you may use `retry` to trigger a build again."),
                                            call(':pushpin: Commit sdf456 has been approved by `user1`\n\n<!-- @user2 r=user1 sdf456 -->')])

    @patch('homu.main.PullReqState')
    def test_review_approved_different_usernames_blank_sha_blocked_by_closed_tree(self, MockPullReqState):
        state = MockPullReqState()
        state.blocked_by_closed_tree.return_value = 1
        state.head_sha = 'sdf456'
        state.title = "My pull request"
        state.repo_label = 'label'
        state.status = 'pending'
        states = {}
        states[state.repo_label] = {'label': state}
        self.assertTrue(action.review_approved(state, True, 'user1', 'user1', 'user2', '', states))
        state.add_comment.assert_has_calls([call(":bulb: This pull request was already approved, no need to approve it again.\n\n- This pull request is currently being tested. If there's no response from the continuous integration service, you may use `retry` to trigger a build again."),
                                            call(':pushpin: Commit sdf456 has been approved by `user1`\n\n<!-- @user2 r=user1 sdf456 -->'),
                                            call(':evergreen_tree: The tree is currently closed for pull requests below priority 1, this pull request will be tested once the tree is reopened')])
        state.change_labels.assert_called_once_with(LabelEvent.APPROVED)

    @patch('homu.main.PullReqState')
    def test_review_approved_same_usernames_sha_different_head_sha(self, MockPullReqState):
        state = MockPullReqState()
        state.head_sha = 'sdf456'
        state.title = "My pull request"
        state.repo_label = 'label'
        state.status = 'pending'
        states = {}
        states[state.repo_label] = {'label': state}
        self.assertTrue(action.review_approved(state, True, 'user', 'user', 'user', 'abcd123', states))

    @patch('homu.main.PullReqState')
    def test_review_rejected(self, MockPullReqState):
        state = MockPullReqState()
        action.review_rejected(state, True)
        self.assertEqual(state.approved_by, '')
        state.save.assert_called_once_with()
        state.change_labels.assert_called_once_with(LabelEvent.REJECTED)

    def test_sha_cmp_equal(self):
        self.assertTrue(action.sha_cmp('f259660', 'f259660b128ae59133dff123998ee9b643aff050'))

    def test_sha_cmp_not_equal(self):
        self.assertFalse(action.sha_cmp('aaabbb12', 'f259660b128ae59133dff123998ee9b643aff050'))

    def test_sha_cmp_short_length(self):
        self.assertFalse(action.sha_cmp('f25', 'f259660b128ae59133dff123998ee9b643aff050'))


if __name__ == '__main__':
    unittest.main()
