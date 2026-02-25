import { Button } from "./Button";

type ApprovalActionsBarProps = {
  disabled?: boolean;
  onApprove: () => void;
  onApproveWithExceptions: () => void;
  onReject: () => void;
};

export function ApprovalActionsBar({ disabled = false, onApprove, onApproveWithExceptions, onReject }: ApprovalActionsBarProps) {
  return (
    <div className="approval-toolbar">
      <div className="approval-toolbar__text">
        <h4>Approval Actions</h4>
        <p>Submit a final decision for this record.</p>
      </div>
      <div className="approval-toolbar__buttons">
        <Button variant="primary" disabled={disabled} onClick={onApprove}>
          Approve
        </Button>
        <Button variant="secondary" disabled={disabled} onClick={onApproveWithExceptions}>
          Approve w/ Exceptions
        </Button>
        <Button variant="danger" disabled={disabled} onClick={onReject}>
          Reject
        </Button>
      </div>
    </div>
  );
}
