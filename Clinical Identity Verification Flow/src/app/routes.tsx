import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { UploadPage } from "./pages/UploadPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { QuizPage } from "./pages/QuizPage";
import { InterviewPage } from "./pages/InterviewPage";
import { SuccessPage } from "./pages/SuccessPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: UploadPage },
      { path: "processing", Component: ProcessingPage },
      { path: "quiz", Component: QuizPage },
      { path: "interview/:id", Component: InterviewPage },
      { path: "success", Component: SuccessPage },
    ],
  },
]);
