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
## Framework for today's talk - forecasting
Organizations of any size need:
- To forecast revenue
- Using a precise approach
- Easily with little complexity
- Providing clear insight — "What changed and Why"
- Establishing and maintaining credibility with stakeholders

---
## Agenda
1. **The Challenge** — statistical issues in operational data
2. **The Structural Solution** — modeling with macroeconomic indices
3. **Building It Right** — functional form, indexation, and regression rigor
4. **Modeling Dynamics** — stationarity, co-integration, and AR models
5. **Using the Forecast** — uncertainty, scenarios, and stakeholder communication
6. **Maintaining the Model** — tracking drift and maintaining accuracy

---
<!-- _class: divider -->
## The Challenge

---
## Statistical Issues
### Top 2 key considerations when modeling:
#### Sampling Bias
- Empirical studies suffer from bias in observational and operational data
- Affects inference, parameter bias, and generalizability
<!-- - Mitigation strategies — setting strata e.g., firmographics, leveraged-outliers -->

#### Simultaneity Bias
- Joint determination of explanatory and dependent variables
- Examples from economics — demand pull inflation
<!-- - Identification strategies: instrumental variables, structural modeling -->

---
## So what do we do about it?
### We need structure
- Naive models inherit these biases — they lack economic grounding
- A **structural approach** decomposes revenue into interpretable, testable components
- Map macro forces → industry dynamics → operational drivers → financial outcomes
- Each layer is independently observable, forecastable, auditable, and composable

---
<!-- _class: divider -->
## The Structural Solution

---
## Dynamic Systems
### A Structural Simplified Linear Approach
- Overcoming differing cyclicality — separate the pro, counter, and a-cyclical components
- Functional form — linearizing PVM: pricing, volume, **mix**
- Implications and opportunities — stability and long-run forecasts
  - Things to monitor — market penetration, share, pricing mix, etc.
---
## System Dynamics
### Modeling Change — generating insight, preventing drift 
- Natural log — log-log, log-level
- Indicator functions — technology transformations, share changes, pricing mix
  - Intercept/s
  - Slope/s 
  - Trend

---
## Indexation — Pricing and Volume Shifts
### Connect public macro data to *your* revenue 
- $Index_t = \sum_{i=1}^n w_i*Industry_i$
- Weighting factors $w_i$: regional, industry, product mix
  - Choice of metric matters — revenue-weighted vs. volume-weighted vs. transaction-weighted
- $Index$ segmentation: firmographics, product categories
- Weights are calibrations — when mix shifts, re-weight or the forecast silently degrades

---
## Model

### Functional Form
  - Revenue is multiplicative: $Revenue_t = \gamma*p_t^{\beta_1}*v_t^{\beta_2}$
  - Logs make it linear: $ln(Revenue_t) = \alpha + \beta_1 * ln(p_t) + \beta_2 * ln(v_t)$
    - Every coefficient directly actionable — scenarios, monitoring, communication
    - Full OLS diagnostic toolkit
    - Returns to scale estimated, not assumed — the data tells you the regime
  - **Trend:** time-varying intercept and elasticities — test with indicators
  - **Seasonality:** periodic (calendar) and non-periodic (Easter, promotions) — both modeled explicitly

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
- Weighting factors:
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
### Identification — can feel like an art form, how to know it's right
- **Specification** — Functional Form drives everything downstream
  - **Omitted Variable Bias** — dropping a variable biases what remains
    (e.g., dropping a collinear predictor that carries unique signal)
  - **Collinearity (VIF)** — individual t-tests become unreliable;
    doesn't mean the model is wrong — check joint significance
  - **Heteroscedasticity** — tells you about the DGP, not just the errors
  - **Autocorrelation** — often the first signal of a missing variable

#### Go/No-Go
- **F-Test** — joint significance holds even when individual t-tests fail
- **Out-of-sample validation** — the only test that matters for forecasting

---
## Regression Modeling — key concepts
### Interpretation and Validation
- **Ceteris paribus** — isolate the effect of one driver, holding others constant
  - The structural decomposition makes this operational, not just theoretical
- **Accuracy metrics** — match the metric to the audience:
  - **MAPE** for stakeholders — "the forecast was off by 0.8%"
  - **MAE** for robustness — resistant to outlier distortion
  - **RMSE** for risk — penalizes for the misses that hurt most
- **Out-of-sample accuracy is the credibility test** — in-sample fit is necessary, not sufficient

---
## Regression Modeling — Key Concepts
### Leveraged Outliers — What's driving your model?
- Leverage: $h_{ii} = x_i'(X'X)^{-1}x_i$ — voting power of each observation
  - $h_{ii}$ near 0 → negligible influence; near 1 → model anchored to this point
  - Flag: $h_{ii} > 2p/n$
- Influence: $\hat{\beta} - \hat{\beta}_{(i)} = \frac{(X'X)^{-1}x_i \cdot e_i}{1 - h_{ii}}$
  - Large shift → this observation is driving your estimates
- **Action:** structural break → indicator (slide 10); data issue → investigate

- $\hat{\beta}_{OLS} = \frac{\sum{(y_i - \bar{y})(x_i - \bar{x})}}{\sum{(x_i - \bar{x})^2}}$; leveraged outlier when both $y_i<<>>\bar{y}$ and $x_i<<>>\bar{x}$

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
### Stationarity — The precondition
- **I(0) vs. I(1)** — does the series revert to a mean, or drift without bound?
  - Get this wrong → spurious regression: high $R^2$, meaningless coefficients
  - Test before modeling — ADF, KPSS
- **Modeling choice:** levels (if stationary or co-integrated) vs. differences

### Co-integration — Validating the structural link
- Integrated processes don't need differencing if the model captures a real equilibrium
  - Co-integration means the linear combination is stationary (residual)
- **Error correction** — deviations from equilibrium self-correct; the forecast adapts

---
## Advanced Time Series Modeling
### ARIMA Errors
- **HAC standard errors** — corrects inference for heteroscedasticity and autocorrelation in one step; $\hat{\beta}$ doesn't change
- **Autocorrelation in residuals is a symptom** — often signals a missing variable (OVB)
  - Fix the specification first; add AR terms only as a last resort
- **Parsimony** — minimum lag order

---
<!-- _class: divider -->
## Using the Forecast

---
## Forecasting
### Forecast Uncertainty
- **Minimize model error** — diagnostic rigor delivers <1% cumulative MAPE on 12-month holdout
- **Forecast error = model error + input forecast error**
  — negligible model error materially improves structural decomposition
- **β × ΔX decomposition** — attribute the forecast to each component: what moved, by how much, and why
- **Macro shocks → revenue impact** — calibrate a GDP or index miss directly to your bottom line
- **Scenarios** — "what if" analysis is where strategy meets forecasting

---
## Forecasting
### Key forecast comparison techniques
- Key Risks and Scenario planning — how you talk to the street
- Current vs. prior — year, forecast, scenario
- Decision-oriented evaluation — financial mitigation analysis


---
<!-- _class: divider -->
## Maintaining the Model

---
## Monitoring and Evaluation
### Evaluation — What the framework enables
- **Performance tracking** — within-year vs. full-year error, error correction, trending to plan                                                                              
- **Early warning** — residual structure and parameter stability signal problems before the forecast misses 
- **Overlay adjustments** — model is the baseline, layer business assumptions on top e.g., large deals, business shifts
- **Model updating** — drift has meaning, meaning has value; update when diagnostics dictate

---
## Monitoring and Evaluation
### Monitoring
What to version and track:
Given a functional form: $y_t = \beta*X_t + \epsilon_t$
Where $\hat{\beta} = (X'X)^{-1}*X'y$
- $y_t$, $\hat{y_t}$, $\epsilon_t$, $X_t$, $MAE$, $MAPE$ — as a versioned table
- $\hat{\beta}$ coefficient vector 
- $\Delta X_t = X_t - X_{t-1}$ — generally correct, and any other transformations
- $\hat{\beta} *\Delta X_t$
 - Holdout $MAPE$ by estimation vintage

---
## Monitoring and Evaluation
### Assumptions That Cause Drift
- Share changes — if your revenue mix shifts, the index weights go stale
- Pricing mix — changes in what's sold at what price point
- Product mix — new products, retired products, category shifts
- Industry composition — your segments grow at different rates
- Regional mix — geographic exposure changes

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
