---
marp: true
theme: uncover
paginate: true
size: 16:9

#header: Retail Forecasting
footer: Bruce Hicks, AMLC Talk March 2026
---
<style>
/* --- Global slide layout --- */
section {
  background: #243133;
  color: navajowhite;
  font-family: Inter, Arial, sans-serif;
  font-size: 26px;
  line-height: 1.35;
  padding: 40px 72px 72px 72px;
  text-align: left;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
}


/* Keep lines from going edge-to-edge */
section > * {
  max-width: 1100px;
}

/* --- Headings: consistent scale + spacing --- */
h1, h2, h3, h4, h5, h6 {
  margin: 0 0 16px 0;
  letter-spacing: -0.02em;
}

h1, h2 {
  margin-top: 0;
  margin-bottom: 24px;
}

h1, h2, h3, h4, h5, h6 {
  text-align: left;
}

h1 { font-size: 56px; line-height: 1.10; }
h2 { font-size: 40px; line-height: 1.15; }
h3 { font-size: 32px; line-height: 1.20; }
h4 { font-size: 26px; margin: 10px 0 8px 0; }

/* --- Paragraphs and lists --- */
p { margin: 0 0 12px 0; }

/* --- Bullet spacing --- */
ul, ol {
  margin-top: 12px;
  margin-left: 0;
  margin-right: auto;
  text-align: left;
  align-self: flex-start;
  width: 100%;
}

li {
  margin-bottom: 16px;
}

/* Optional: tighter nested bullets */
li ul li,
li ol li {
  margin-bottom: 10px;
}

/* --- Emphasis --- */
strong { color: #e9fffb; }

/* --- Code and math readability --- */
code { font-size: 0.90em; }
mjx-container { font-size: 1.0em; }

/* --- Header / Footer positioning --- */
header, footer {
  position: absolute;
  left: 72px;
  right: 72px;
  font-size: 16px;
  opacity: 0.25;
  color: navajowhite;
}

header { top: 18px; }
footer { bottom: 18px; }

header, footer {
  text-align: right;
}

section::after {
  font-size: 16px;
  opacity: 0.7;
}

/* --- Title slide class --- */
section.title {
  padding-top: 84px;
}

section.title h1 {
  font-size: 68px;
  margin-bottom: 10px;
}

section.title h3 {
  font-size: 28px;
  opacity: 0.95;
  margin-top: 8px;
}

/* Align title text for right-side background image */
section.title > * {
  max-width: 760px;
}
/* --- Section divider slides --- */
section.divider {
  justify-content: center;
  align-items: center;
  text-align: center;
}

section.divider h2 {
  text-align: center;
  font-size: 52px;
}

/* --- Mermaid diagrams --- */
.mermaid {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  flex: 1;
}

.mermaid svg {
  max-width: 100%;
  max-height: 100%;
  height: auto;
}
</style>

<!-- Mermaid renderer (HTML/PDF via Chromium). -->
<script src="js/mermaid.min.js"></script>
<script>
  mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    flowchart: {
      htmlLabels: false,
      nodeSpacing: 60,
      rankSpacing: 100,
      curve: 'basis',
      padding: 20
    },
    themeVariables: {
      fontFamily: 'Inter, Arial, sans-serif',
      fontSize: '30px',
      background: '#243133',
      primaryColor: '#1f2a2c',
      primaryBorderColor: '#8fe0d6',
      primaryTextColor: '#e9fffb',
      lineColor: '#8fe0d6',
      secondaryColor: '#243133',
      tertiaryColor: '#243133',
      nodePadding: '25',
      nodeTextSize: '30px'
    }
  });
</script>

<!-- _class: title -->

![bg](images/Cover_Slide.png)

# Payments Forecasting with Retail Data
### Scaling insights with an interpretable, drift-resistant solution of a dynamic system

---
## Who am I?
- Bruce Hicks – Founder and Principal, est8ic.ai
- 15+ years of experience in ML, forecasting and economic analysis
- Working with Global FinTech companies
- Started my career in technology-enabled manufacturing

---
## Motivation for today's talk – key question
Organizations of any size need:
- To forecast revenue
- Using a precise approach — preferably <1% 1-step annual forecast error
- Easily with little complexity
- Providing clear insight — "What changed and Why"
- To establish and maintain credibility with stakeholders

---
## Agenda
1. **The Problem** — statistical issues in operational data
2. **The Structural Solution** — modeling with macroeconomic indices
3. **Building It Right** — functional form, indexation, and regression rigor
4. **Modeling Dynamics** — stationarity, co-integration, and AR models
5. **Using the Forecast** — uncertainty, scenarios, and stakeholder communication
6. **Maintaining the Model** — tracking drift and maintaining accuracy

---
<!-- _class: divider -->
## The Problem

---
## Statistical Issues
### Top 2 key considerations when modeling:
#### Sampling Bias
- Empirical studies suffer from bias in observational and operational data
- Affects inference, parameter bias, and generalizability
- Mitigation strategies — setting strata e.g., firmographics, leveraged-outliers

#### Simultaneity Bias
- Joint determination of explanatory and dependent variables
- Examples from economics — demand pull inflation
- Identification strategies: instrumental variables, structural modeling

---
## So what do we do about it?
### We need structure
- Naive models inherit all these biases — they lack economic grounding
- A **structural approach** decomposes revenue into interpretable, testable components
- Map macro forces → industry dynamics → operational drivers → financial outcomes
- Each layer is independently observable, forecastable, auditable, and composable

---
<!-- _class: divider -->
## The Structural Solution

---
## Dynamic Systems
### A Structural Simplified Linear Approach
- Overcoming differing cyclicality — separating into pro, counter, and a-cyclical components
- When linear approximations break down — pricing, volume, **mix** (PVM)
- Implications and opportunities — stability and long-run forecasts
  - Things to monitor — penetration, share change, pricing mix, etc.
---
## System Dynamics
### Transformations
- Natural log — log-log, log-level
- Indicator functions — technology transformations, share changes, pricing mix
  - Intercept/s
  - Slope/s 
  - Trend

---
## Indexation — pricing and volume shifts
### Business Weighted Indices 
- $Index_t = \sum_{i=1}^n w_i*Industry_i$
- Weighing factors $w_i$: regional, industry, product mix
- $Index$ construction methodologies: firmographics, product categories

---
## Model

### Functional Form
- If we start with: $Revenue_t = \gamma*p_t^{\beta_1}*v_t^{\beta_2}$
- $ln(Revenue_t) = \alpha + \beta_1 * ln(p_t) + \beta_2 * ln(v_t)$, $\alpha = ln(\gamma)$
  - log normal standard errors
  - reduce the impact of collinearity
  - diminishing returns to scale
- Trend: Time varying intercept and elasticities can and should be tested
- Seasonality: retail is highly 'seasonal' at both periodic and non-periodic time intervals

---
## Model

### Index approach

<div class="mermaid">
flowchart LR
  classDef largeNode fill:#1f2a2c,stroke:#8fe0d6,stroke-width:2px,color:#e9fffb,font-size:34px;
  A("Macroeconomy<br>GDP"):::largeNode -->
  B("Industry demand<br>Retail index"):::largeNode
  B --> C("Operational driver<br>Volume"):::largeNode
  C --> D("Financial outcome<br>Revenue"):::largeNode
</div>


---
## Model

### Index approach

<div class="mermaid">
flowchart LR
  classDef largeNode fill:#1f2a2c,stroke:#8fe0d6,stroke-width:2px,color:#e9fffb,font-size:34px;
  A("Economic<br>Growth"):::largeNode -->
  B("E-Commerce"):::largeNode
  B --> C("Industry<br>Volume"):::largeNode
  C --> D("Segment<br>Revenue"):::largeNode
</div>

<div class="mermaid">
flowchart LR
  classDef largeNode fill:#1f2a2c,stroke:#8fe0d6,stroke-width:2px,color:#e9fffb,font-size:34px;
  A("Economic<br>Growth"):::largeNode -->
  B("Full Service<br>Restaurant"):::largeNode
  B --> C("Industry<br>Volume"):::largeNode
  C --> D("Segment<br>Revenue"):::largeNode
</div>

<div class="mermaid">
flowchart LR
  classDef largeNode fill:#1f2a2c,stroke:#8fe0d6,stroke-width:2px,color:#e9fffb,font-size:34px;
  A("Economic<br>Growth"):::largeNode -->
  B("Grocery"):::largeNode
  B --> C("Industry<br>Transactions"):::largeNode
  C --> D("Segment<br>Revenue"):::largeNode
</div>

---
## Industry Index
### Pricing Mix
- $Industry_{mix_t} = \sum_{i=1}^n w_i*Industry_i$
- Weighing factors:
<div class="mermaid">
sankey-beta
  FSR,Revenue,40
  QSR,Revenue,30
  General Retail,Revenue,15
  Grocery,Revenue,10
  Other,Revenue,5
</div>


---
<!-- _class: divider -->
## Building It Right

---
## Regression Modeling — key concepts
### Identification — can feel like an art form
- Regression through the origin — affine is fine
- Model specification — generally functional form
- Omitted Variable Bias — e.g., omitted seasonal effects or dropping a collinear predictor that carries unique signal
- Collinearity ViF — interpretation of individual significance: @1, 5, 10%
- Heteroscedasticity of error terms — e.g., wages vs. education
- Autocorrelation — often due to OVB
#### Go/No-Go tests
- F-Test — testing the joint distribution; joint significance can hold even when individual t-tests fail under collinearity
- Out-of-sample validation and backtesting

---
## Regression Modeling — key concepts
### Interpretation, assumptions, and testing (1):
- Ceteris paribus — all else equal; interpret each coefficient holding others constant
- Relative accuracy metrics:
  - **MAPE** — scale-independent, intuitive for stakeholders ("X%")
  - **MAE** — robust to outliers, units of the dependent variable
  - **RMSE** — penalizes large errors, useful for risk-sensitive forecasts
- In-sample fit vs. out-of-sample accuracy — the latter is what matters

---
## Regression Modeling — key concepts
### Interpretation, assumptions, and testing (2):
- Leveraged outliers — not just outliers
  - $\hat{\beta_i} = \frac{\sum{(y_i - \bar{y})(x_i - \bar{x})}}{\sum{(x_i - \bar{x})^2}}$; both $y_i<<>>\bar{y}$ and $x_i<<>>\bar{x}$
- Leave one out cross-validation
  - $\hat{\beta} - \hat{\beta_i} = \frac{(X'X)^{-1}x_i * e_i}{1-h_{ii}}$ compare the full sample $\beta$ to the leave one out $\beta_i$
  - $\hat{h_{ii}} = x'(X'X)^{-1}x_i$ - how voting power does each observation have
    - $h_{ii}$ close to 0 → the line barely notices it
    - $h_{ii}$ close to 1 → the regression line must pass near it because there's nothing else counterbalancing it
    - Rule of thumb: $h_ii > 2p/n$ (twice the average) means "this point has outsized pull"

---
## Regression Modeling — key concepts
### Other key concepts
- Causal inference — identifying causal relationships
- Instrumental variables — addressing endogeneity e.g., 2SLS
- Difference-in-differences — comparing treatment and control groups
- Regression discontinuity design — exploiting discontinuities in treatment assignment

---
<!-- _class: divider -->
## Modeling Dynamics

---
## Advanced Time Series Modeling
### I(0) vs. I(1)
- Stationary vs. integrated processes
- Testing and diagnostics
- Modeling implications for levels vs. differences

### Co-integration Concepts
- Economic and operational interpretations
- Long-run equilibrium relationships
- Error-correction mechanisms


---
## Advanced Time Series Modeling
### AR(p) Models
- Standard errors: OLS and HAC vs. AR(p) — HAC corrects inference (SEs, p-values) without changing $\hat{\beta}$
- Higher-order autoregressive dynamics in model error — presence often signifies OVB
- Lag selection — use the principle of parsimony
- Hold out validation — most recent full year


---
<!-- _class: divider -->
## Using the Forecast

---
## Forecasting
### Forecast Uncertainty
- Model error + input (exogenous) forecast error = forecast error
- Error propagation through dynamic systems — ACF/PACF and IRF
- Scenario-based sensitivity analysis

---
## Forecasting
### Key Forecast Comparison Techniques
- Key Risks and Scenario planning — how you talk to the street
- Current vs. prior — year, forecast, scenario
- Decision-oriented evaluation — financial mitigation analysis


---
<!-- _class: divider -->
## Maintaining the Model

---
## Monitoring and Evaluation
### Evaluation
- Model monitoring and performance tracking — within year vs. full year trend in forecast error
- Early warning signals and anomaly detection
- Adaptive forecasting strategies
- Model re-estimation and updating

---
## Monitoring and Evaluation
### Monitoring
Inventory of items I like to store and track:
Given a functional form: $y_t = \beta*X_t + \epsilon_t$
Where $\beta = (X'X)^{-1}*X'y$
- $y_t$, $\hat{y_t}$, $\epsilon_t$, $X_t$, $MAE$, $MAPE$ — as a versioned table
- $\matrix{\beta}$ coefficient vector 
- $\Delta X_t = X_t - X_{t-1}$ — generally correct, and any other transformations
- $\beta *\Delta X_t$

---
## Monitoring and Evaluation
### Monitoring — other key assumptions that can cause drift:
- Share changes
- Pricing mix
- Product mix
- Industry composition
- Regional mix

---
## Key Takeaways
- **Structure over complexity** — decompose revenue through macro → industry → operational → financial layers for interpretable, drift-resistant forecasts
- **Regression rigor matters** — proper identification, diagnostics, and out-of-sample validation separate credible forecasts from fragile ones
- **Monitor the assumptions** — share changes, pricing mix, and industry composition drift will break even well-specified models if untracked
- **Communicate uncertainty** — scenarios and comparison frameworks build stakeholder credibility over point forecasts

---
## Questions?

### Thank you

Bruce Hicks
Founder and Principal, est8ic.ai
