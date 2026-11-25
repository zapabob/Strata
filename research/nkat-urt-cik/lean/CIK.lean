import Std

namespace CIK

/-- The observed support ties the future input to the first input. -/
theorem causal_on_diagonal :
    ∃ q : Bool → Bool, ∀ a : Bool, q a = a := by
  exact ⟨id, fun _ => rfl⟩

/-- Keeping the first input fixed and varying the future defeats that extension. -/
theorem no_causal_extension :
    ¬ ∃ q : Bool → Bool, q false = false ∧ q false = true := by
  rintro ⟨q, h₀, h₁⟩
  exact Bool.noConfusion (h₀.symm.trans h₁)

/-- A rational grid version of the binary past-output TV bound. -/
theorem binary_tv_radius (scale q : Nat) (hq : q ≤ scale) :
    scale ≤ 2 * max q (scale - q) := by
  have left := Nat.le_max_left q (scale - q)
  have right := Nat.le_max_right q (scale - q)
  omega

/-- A stabilised recurrence stays at the first fixed point it reaches. -/
theorem recurrence_stays_fixed {α : Type} (step : α → α) (v : Nat → α)
    (next : ∀ k, v (k + 1) = step (v k))
    (n : Nat) (fixed : v (n + 1) = v n) (r : Nat) : v (n + r) = v n := by
  induction r with
  | zero => rfl
  | succ r ih =>
    calc
      v (n + (r + 1)) = step (v (n + r)) := by
        simpa only [Nat.add_assoc] using next (n + r)
      _ = step (v n) := congrArg step ih
      _ = v n := (next n).symm.trans fixed

/-- A chain starting at positive dimension and growing strictly at every non-fixed
    step must reach equality before the ambient dimension. -/
theorem bounded_growth_has_fixed_step {α : Type} [DecidableEq α] (v : Nat → α)
    (dim : α → Nat) (cap : Nat) (initial : 0 < dim (v 0))
    (bounded : ∀ k, dim (v k) ≤ cap)
    (grows : ∀ k, v (k + 1) ≠ v k → dim (v k) < dim (v (k + 1))) :
    ∃ k, k < cap ∧ v (k + 1) = v k := by
  have progress (k : Nat) :
      (∃ j, j < k ∧ v (j + 1) = v j) ∨ k + 1 ≤ dim (v k) := by
    induction k with
    | zero => exact Or.inr initial
    | succ k ih =>
      rcases ih with ⟨j, hj, fixed⟩ | lower
      · exact Or.inl ⟨j, Nat.lt_trans hj (Nat.lt_succ_self k), fixed⟩
      · by_cases fixed : v (k + 1) = v k
        · exact Or.inl ⟨k, Nat.lt_succ_self k, fixed⟩
        · have strict := grows k fixed
          exact Or.inr (by omega)
  rcases progress cap with reached | impossible
  · exact reached
  · have upper := bounded cap
    omega

private theorem fin3_cases (i : Fin 3) : i = 0 ∨ i = 1 ∨ i = 2 := by
  by_cases h₀ : i.val = 0
  · exact Or.inl (Fin.ext h₀)
  by_cases h₁ : i.val = 1
  · exact Or.inr (Or.inl (Fin.ext h₁))
  have bound := i.isLt
  have h₂ : i.val = 2 := by omega
  exact Or.inr (Or.inr (Fin.ext h₂))

/-- Integers representing conditional probabilities with common denominator 12. -/
def posterior (positive : Bool) (i j : Fin 3) : Int :=
  if i = j then (if positive then 6 else 2) else (if positive then 3 else 5)

def rowSum (positive : Bool) (i : Fin 3) : Int :=
  posterior positive i 0 + posterior positive i 1 + posterior positive i 2

def gram (positive : Bool) (i j : Fin 3) : Int :=
  posterior positive 0 i * posterior positive 0 j +
  posterior positive 1 i * posterior positive 1 j +
  posterior positive 2 i * posterior positive 2 j

def rowMax (positive : Bool) (i : Fin 3) : Int :=
  max (posterior positive i 0) (max (posterior positive i 1) (posterior positive i 2))

/-- Each verifier choice has probability at most the best single choice. -/
theorem posterior_le_row_max (positive : Bool) (i j : Fin 3) :
    posterior positive i j ≤ rowMax positive i := by
  cases positive <;> rcases fin3_cases i with rfl | rfl | rfl <;>
    rcases fin3_cases j with rfl | rfl | rfl <;> decide

/-- The best single-choice score is attained in each row. -/
theorem posterior_row_max_attained (positive : Bool) (i : Fin 3) :
    ∃ j, posterior positive i j = rowMax positive i := by
  cases positive with
  | false =>
    rcases fin3_cases i with rfl | rfl | rfl
    · exact ⟨1, by decide⟩
    · exact ⟨0, by decide⟩
    · exact ⟨0, by decide⟩
  | true =>
    rcases fin3_cases i with rfl | rfl | rfl
    · exact ⟨0, by decide⟩
    · exact ⟨1, by decide⟩
    · exact ⟨2, by decide⟩

/-- For a uniform signal, divide this sum by 36 to obtain one-attempt success. -/
def oneAttemptNumerator (positive : Bool) : Int :=
  rowMax positive 0 + rowMax positive 1 + rowMax positive 2

theorem posterior_rows_normalise (i : Fin 3) :
    rowSum true i = 12 ∧ rowSum false i = 12 := by
  rcases fin3_cases i with rfl | rfl | rfl <;> decide

theorem posterior_same_gram : gram true = gram false := by
  funext i j
  rcases fin3_cases i with rfl | rfl | rfl <;>
    rcases fin3_cases j with rfl | rfl | rfl <;> decide

theorem posterior_different_success :
    oneAttemptNumerator true = 18 ∧ oneAttemptNumerator false = 15 := by
  decide

/-- The full Gram matrix, dimension and budget fail to determine success. -/
theorem no_universal_gram_law
    (f : Nat → Nat → (Fin 3 → Fin 3 → Int) → Int)
    (positive : f 1 3 (gram true) = oneAttemptNumerator true)
    (negative : f 1 3 (gram false) = oneAttemptNumerator false) : False := by
  rw [posterior_same_gram] at positive
  have scores := positive.symm.trans negative
  rw [posterior_different_success.1, posterior_different_success.2] at scores
  exact (by decide : (18 : Int) ≠ 15) scores

/-- Canonical unary proof length under a verifier that admits precisely that length. -/
theorem canonical_proof_budget (length budget : Nat) :
    (∃ candidate, candidate = length ∧ candidate ≤ budget) ↔ length ≤ budget := by
  constructor
  · rintro ⟨candidate, rfl, hb⟩
    exact hb
  · intro hb
    exact ⟨length, rfl, hb⟩

/-- Two unit disturbances have the same separate energies for either second sign. -/
theorem temporal_cross_term_control :
    (1 : Int)^2 + (1 : Int)^2 = (1 : Int)^2 + (-1 : Int)^2 ∧
    (1 : Int)^2 + (1 + 1 : Int)^2 = 5 ∧
    (1 : Int)^2 + (1 - 1 : Int)^2 = 1 := by
  decide

#print axioms causal_on_diagonal
#print axioms no_causal_extension
#print axioms binary_tv_radius
#print axioms recurrence_stays_fixed
#print axioms bounded_growth_has_fixed_step
#print axioms posterior_rows_normalise
#print axioms posterior_le_row_max
#print axioms posterior_row_max_attained
#print axioms posterior_same_gram
#print axioms posterior_different_success
#print axioms no_universal_gram_law
#print axioms canonical_proof_budget
#print axioms temporal_cross_term_control

end CIK
