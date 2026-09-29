"""Plain-language evidence templates; no ground-truth membership is available here."""
import numpy as np

from app.predict.features import Features, FEATURE_NAMES


def reason(text: str, source: str, feature: str | None = None, contribution: float | None = None) -> dict:
    return {'text': text, 'source_group': source, 'feature': feature, 'contribution': contribution}


def feature_reason(features: Features, row: int, values: np.ndarray, index: int, contribution: float) -> dict:
    value = float(values[index])
    templates = [
        (f'This ATM is {value:.2f} km from the nearest observed terminal account home-district centre.', 'holders'),
        (f'Chain-linked accounts made {value:.0f} withdrawals here in the last 7 days.', 'withdrawals_7d'),
        (f'Chain-linked accounts made {value:.0f} withdrawals here in the last 30 days.', 'withdrawals_30d'),
        (f'Past chain-linked withdrawals give this ATM a KDE density of {value:.5f} per square km.', 'past_withdrawals'),
        (f'The observed money trail reaches terminal accounts after {value:.0f} transfer hops.', 'trace'),
        (f'The largest temporal burst score among chain accounts is {value:.2f}.', 'temporal'),
        (f'The prediction was made during hour {value:.0f}:00 IST.', 'complaint'),
        (f'The prediction day is {features.clock.strftime("%A")}.', 'complaint'),
        ('This ATM is in a different district from the latest chain-linked withdrawal.' if value
         else 'This ATM shares the latest chain-linked withdrawal district (or no prior district is known).', 'last_withdrawal'),
    ]
    text, source = templates[index]
    direction = 'raises' if contribution > 0 else 'lowers' if contribution < 0 else 'does not change'
    return reason(f'{text} This feature {direction} the model score.', source, FEATURE_NAMES[index], float(contribution))


def explanations(features: Features, row: int, model: str, matrix: np.ndarray,
                 contributions: np.ndarray | None, bandwidth: float, train_n: int,
                 expected_atms: float, hours: int, fallback: str | None) -> list[dict]:
    if model == 'xgboost' and contributions is not None:
        top = np.argsort(-np.abs(contributions[row, :-1]), kind='stable')[:3]
        return [feature_reason(features, row, matrix[row], int(i), float(contributions[row, i])) for i in top]
    age = features.last_age_days[row]
    recency = (f'Chain-linked accounts last withdrew here {age:.2f} days before prediction.'
               if np.isfinite(age) else 'No earlier chain-linked withdrawal was observed at this ATM.')
    first = reason(fallback, 'past_withdrawals') if fallback else (
        reason(f'KDE uses {len(features.history)} past chain-linked withdrawals with a {bandwidth:g} km bandwidth.', 'past_withdrawals')
        if model == 'kde' else reason(recency, 'atm_withdrawals'))
    second = reason(recency, 'atm_withdrawals') if fallback or model == 'kde' else reason(
        f'Chain-linked accounts made {matrix[row, 2]:.0f} withdrawals here in the last 30 days.', 'withdrawals_30d')
    third = reason(f'{train_n} earlier completed training cases imply {expected_atms:.3f} cash-out ATMs per case in the next {hours} hours. '
                   'This is a recency/density-based probability estimate, not a calibrated guarantee.' if train_n else
                   'No earlier completed training cases are available; the estimate uses an explicit uniform time prior.', 'training')
    return [first, second, third]
