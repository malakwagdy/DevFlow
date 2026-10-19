import { useId } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import Page from '../components/layout/Page';
import AsyncContent from '../components/ui/AsyncContent';
import Button from '../components/ui/Button';
import FormField from '../components/ui/FormField';
import Icon from '../components/ui/Icon';
import SegmentedControl from '../components/ui/SegmentedControl';
import { ROUTES } from '../config/navigation';
import useApi from '../hooks/useApi';
import { api } from '../services/api';

const SIGN_IN = 'signin';
const SIGN_UP = 'signup';

function SignInForm({ credentials, submitLabel, onSubmit }) {
  const emailId = useId();
  const passwordId = useId();
  return (
    <form className="form" onSubmit={onSubmit}>
      <FormField label="Work Email" htmlFor={emailId}>
        <input id={emailId} type="email" required className="input" placeholder="alex@company.corp" defaultValue={credentials.email} />
      </FormField>
      <FormField
        label="Password"
        htmlFor={passwordId}
        action={
          <a href="#" className="text-link" onClick={(event) => event.preventDefault()}>
            Forgot password?
          </a>
        }
      >
        <input id={passwordId} type="password" required className="input" defaultValue={credentials.password} />
      </FormField>
      <Button type="submit" block className="auth-card__submit">
        {submitLabel}
      </Button>
    </form>
  );
}

function SignUpForm({ placeholders, submitLabel, onSubmit }) {
  const nameId = useId();
  const emailId = useId();
  const passwordId = useId();
  return (
    <form className="form" onSubmit={onSubmit}>
      <FormField label="Full Name" htmlFor={nameId}>
        <input id={nameId} type="text" required className="input" placeholder={placeholders.name} />
      </FormField>
      <FormField label="Work Email" htmlFor={emailId}>
        <input id={emailId} type="email" required className="input" placeholder={placeholders.email} />
      </FormField>
      <FormField label="Password" htmlFor={passwordId}>
        <input id={passwordId} type="password" required className="input" placeholder={placeholders.password} />
      </FormField>
      <Button type="submit" block className="auth-card__submit">
        {submitLabel}
      </Button>
    </form>
  );
}

export default function AuthPage() {
  const state = useApi(api.getAuthContent);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const mode = searchParams.get('mode') === SIGN_IN ? SIGN_IN : SIGN_UP;

  const setMode = (nextMode) => setSearchParams(nextMode === SIGN_IN ? { mode: SIGN_IN } : {}, { replace: true });

  const handleSubmit = (event) => {
    event.preventDefault();
    navigate(ROUTES.projects);
  };

  return (
    <Page variant="auth">
      <AsyncContent state={state}>
        {({ modes, demoCredentials, placeholders }) => {
          const copy = modes[mode];
          const otherMode = mode === SIGN_IN ? SIGN_UP : SIGN_IN;
          return (
            <div className="auth-card">
              <div className="auth-card__head">
                <Link to={ROUTES.landing} className="auth-card__brand">
                  <Icon name="rocket_launch" />
                  DevFlow
                </Link>
                <h1 className="auth-card__title">{copy.headline}</h1>
                <p className="auth-card__subtitle">{copy.subhead}</p>
              </div>

              <div className="auth-card__tabs">
                <SegmentedControl
                  block
                  label="Authentication mode"
                  value={mode}
                  onChange={setMode}
                  options={[
                    { value: SIGN_IN, label: modes.signin.tabLabel },
                    { value: SIGN_UP, label: modes.signup.tabLabel },
                  ]}
                />
              </div>

              {mode === SIGN_IN ? (
                <SignInForm credentials={demoCredentials} submitLabel={copy.submitLabel} onSubmit={handleSubmit} />
              ) : (
                <SignUpForm placeholders={placeholders} submitLabel={copy.submitLabel} onSubmit={handleSubmit} />
              )}

              <div className="auth-card__switch">
                {copy.switchPrompt}{' '}
                <button type="button" className="text-link text-link--medium" onClick={() => setMode(otherMode)}>
                  {copy.switchAction}
                </button>
              </div>
            </div>
          );
        }}
      </AsyncContent>
    </Page>
  );
}
