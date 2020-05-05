import { api } from "@/api";
import { Action, Module, Mutation, VuexModule } from "vuex-module-decorators";
import { IComponents, IStudyShow } from "@/interfaces";
import { mainStore } from "@/utils/store-accessor";

@Module({ name: "study" })
export default class StudyModule extends VuexModule {
  facts: IComponents["Fact"][] = [];
  decks: IComponents["Deck"][] = [];
  schedule: IComponents["Schedule"][] = [];
  recommendation = false;
  show: IStudyShow = { text: "loading", enable_report: false, enable_actions: false };
  frontTime = 0;
  time = 0;
  timer: number | undefined;
  backTime = 0;

  get deckIds() {
    return this.decks.map((deck) => deck.id);
  }

  @Mutation
  addToSchedule(
    fact_id: number,
    typed: string,
    response: boolean,
    elapsed_seconds_text: number,
    elapsed_seconds_answer: number,
  ) {
    this.schedule.push({
      fact_id: fact_id,
      typed: typed,
      response: response,
      elapsed_seconds_text: elapsed_seconds_text,
      elapsed_seconds_answer: elapsed_seconds_answer,
    });
  }

  @Mutation
  emptySchedule() {
    this.schedule = [];
  }

  @Mutation
  setRecommendation(payload: boolean) {
    this.recommendation = payload;
  }

  @Mutation
  setShow(payload: IComponents["Fact"]) {
    this.show = {
      text: payload.text,
      fact: payload,
      enable_report: true,
      enable_actions: true,
    };
    this.startTimer();
  }

  @Mutation
  setShowLoading() {
    this.show = { text: "Loading...", enable_report: false, enable_actions: false };
  }

  @Mutation
  setShowEmpty() {
    this.show = {
      text: "You have finished studying these decks for now, check back in later!",
      enable_report: false,
      enable_actions: false,
    };
  }

  @Mutation
  setShowError() {
    this.show = {
      text: "A problem occurred, check back in later!",
      enable_report: false,
      enable_actions: false,
    };
  }

  @Mutation
  setFacts(payload: IComponents["Fact"][]) {
    this.facts = payload;
  }

  @Mutation
  removeFirstFact() {
    this.facts.shift();
  }

  @Mutation
  loading() {
    this.show = { text: "loading", enable_report: false, enable_actions: false };
  }

  @Mutation
  updateTimer() {
    this.time++;
  }

  @Mutation
  resetTimer() {
    clearInterval(this.timer);
    this.time = 0;
  }

  @Mutation
  startTimer() {
    this.timer = setInterval(() => this.updateTimer(), 1000);
  }

  @Mutation
  markFrontTime() {
    this.frontTime = this.time;
    this.resetTimer();
  }

  @Mutation
  markBackTime() {
    this.backTime = this.time;
    this.resetTimer();
  }

  @Action
  async getNextShow() {
    this.resetTimer();
    if (this.facts.length > 0) {
      this.setShow(this.facts[0]);
      this.removeFirstFact();
    } else {
      await this.getFacts();
    }
  }

  @Action
  async getFacts() {
    this.resetTimer();
    try {
      this.setShowLoading();
      const response = await api.getStudyFacts(mainStore.token, this.deckIds);
      if (response.data.length == 0) {
        this.setShowEmpty();
        this.setFacts([]);
      } else {
        this.setFacts(response.data);
        await this.getNextShow();
      }
    } catch (error) {
      await mainStore.checkApiError(error);
      console.log(error)
      this.setShowError();
    }
  }

  @Action
  async suspendFact() {
    this.resetTimer();
    if (this.show.fact && this.show.enable_actions) {
      try {
        await api.suspendFact(mainStore.token, this.show.fact.fact_id);
        await this.getNextShow();
      } catch (error) {
        await mainStore.checkApiError(error);
      }
    }
  }

  @Action
  async reportFact() {
    this.resetTimer();
    if (this.show.fact && this.show.enable_report) {
      try {
        await api.reportFact(mainStore.token, this.show.fact.fact_id);
        await this.getNextShow();
      } catch (error) {
        await mainStore.checkApiError(error);
      }
    }
  }

  @Action
  async deleteFact() {
    this.resetTimer();
    if (this.show.fact && this.show.enable_actions) {
      try {
        await api.deleteFact(mainStore.token, this.show.fact.fact_id);
        await this.getNextShow();
      } catch (error) {
        await mainStore.checkApiError(error);
      }
    }
  }

  @Action
  async evaluateAnswer(typed: string) {
    console.log("Evaluate ANSWER");
    if (this.show.fact && this.show.enable_actions) {
      try {
        this.markFrontTime();
        const response = await api.evalAnswer(
          mainStore.token,
          this.show.fact.fact_id,
          typed,
        );
        this.setRecommendation(response.data);
        this.startTimer();
      } catch (error) {
        await mainStore.checkApiError(error);
      }
    }
  }

  @Action
  async updateSchedule() {
    if (this.show.fact && this.show.enable_actions) {
      try {
        await api.updateSchedule(mainStore.token, this.schedule);
        this.emptySchedule();
        await this.getNextShow();
      } catch (error) {
        await mainStore.checkApiError(error);
      }
    }
  }
}
